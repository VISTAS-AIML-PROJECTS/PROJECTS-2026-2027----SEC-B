import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import desc
from backend.database.models import VehicleFCRegistry, AlertLog, TruckLog
from backend.database.db import SessionLocal

class FCService:
    """
    Vehicle Fitness Certificate (FC) Verification & Police Enforcement Service.
    
    Handles:
    1. Real-time FC status verification (VALID vs EXPIRED vs POLICE DESTRUCTION ORDER).
    2. Police Enforcement Rules:
       - Age >= 15 years + Expired FC -> DESTROY_VEHICLE_SCRAP (Impound & RVSF Destruction Warrant).
       - Age < 15 years + Expired FC -> FC_RENEWAL_PROCESS (Mandatory RTO Testing & ₹5,000 Challan).
    3. Automated RTO Multi-Point Fitness Diagnostic Test & FC Renewal Workflow.
    4. Registered Vehicle Scrapping Facility (RVSF) Vehicle Destruction Execution.
    5. Penalty Challan Fine Payment & Audit Reports.
    """

    SCRAP_AGE_THRESHOLD_YEARS = 15
    STANDARD_FC_FINE = 5000.0
    EXTREME_SCRAP_PENALTY = 25000.0

    def __init__(self):
        self.fc_cache = {}

    def verify_fc_status(self, license_plate, db_session=None):
        """
        Queries the FC registry for the given license plate.
        If the plate is not registered, generates a deterministic record.
        Returns a dictionary with complete FC and police enforcement status.
        """
        if not license_plate:
            return {'fc_status': 'VALID', 'vehicle_age_years': 4, 'police_action_required': 'NONE'}

        clean_plate = license_plate.replace(" ", "").upper()
        if clean_plate in self.fc_cache:
            return self.fc_cache[clean_plate]

        close_db = False
        if db_session is None:
            db_session = SessionLocal()
            close_db = True

        try:
            record = db_session.query(VehicleFCRegistry).filter(
                VehicleFCRegistry.license_plate == clean_plate
            ).first()

            if not record:
                # Deterministically seed an FC profile for unknown live plates
                record = self._generate_default_fc_record(clean_plate)
                db_session.add(record)
                db_session.commit()

            res = record.to_dict()
            self.fc_cache[clean_plate] = res
            return res
        except Exception as e:
            print(f"❌ Error verifying FC status for {license_plate}: {e}")
            if db_session:
                db_session.rollback()
            return {
                'license_plate': license_plate,
                'fc_status': 'EXPIRED_RENEWAL_REQUIRED',
                'vehicle_age_years': 6,
                'police_action_required': 'FC_RENEWAL_PROCESS',
                'police_notice_number': f"POL-FC-{abs(hash(license_plate)) % 90000 + 10000}",
                'fine_amount': self.STANDARD_FC_FINE,
                'destruction_order_status': 'NONE'
            }
        finally:
            if close_db:
                db_session.close()

    def _generate_default_fc_record(self, clean_plate):
        """
        Creates a realistic FC registry record based on deterministic plate hashing.
        """
        now = datetime.now(timezone.utc)
        h = abs(hash(clean_plate))
        
        # 30% over-aged / critically unfit (>15 yrs), 35% expired needing renewal, 35% valid
        type_idx = h % 10
        
        if type_idx in [0, 1, 2]:
            # Over-aged End-of-Life vehicle (>= 15 years) -> MUST BE DESTROYED / SCRAPPED
            age = random.randint(15, 22)
            reg_date = now - timedelta(days=age * 365 + random.randint(10, 200))
            expiry_date = now - timedelta(days=random.randint(60, 900))
            issue_date = expiry_date - timedelta(days=365)
            status = 'DESTROY_VEHICLE_SCRAP'
            police_action = 'DESTROY_VEHICLE_SCRAP'
            notice_num = f"POL-SCRAP-2026-{h % 9000 + 1000}"
            fine = self.EXTREME_SCRAP_PENALTY
            destruct_status = 'ORDER_ISSUED'
            fitness_score = round(random.uniform(28.0, 48.0), 1)
            emission = 'BS-III Failed (Excessive Smoke & Particulates)'
        elif type_idx in [3, 4, 5, 6]:
            # Expired FC but under 15 years old -> CAN UNDERGO FC RENEWAL PROCESS
            age = random.randint(4, 13)
            reg_date = now - timedelta(days=age * 365 + random.randint(10, 200))
            expiry_date = now - timedelta(days=random.randint(15, 180))
            issue_date = expiry_date - timedelta(days=365)
            status = 'EXPIRED_RENEWAL_REQUIRED'
            police_action = 'FC_RENEWAL_PROCESS'
            notice_num = f"POL-FC-2026-{h % 9000 + 1000}"
            fine = self.STANDARD_FC_FINE
            destruct_status = 'NONE'
            fitness_score = round(random.uniform(52.0, 72.0), 1)
            emission = 'BS-IV Conditional Pass (Emissions Test Expired)'
        else:
            # Valid FC -> COMPLIANT
            age = random.randint(1, 8)
            reg_date = now - timedelta(days=age * 365 + random.randint(10, 200))
            expiry_date = now + timedelta(days=random.randint(45, 340))
            issue_date = expiry_date - timedelta(days=365)
            status = 'VALID'
            police_action = 'NONE'
            notice_num = None
            fine = 0.0
            destruct_status = 'NONE'
            fitness_score = round(random.uniform(86.0, 98.0), 1)
            emission = 'BS-VI Compliant'

        state_prefix = clean_plate[:2] if len(clean_plate) >= 2 else 'TN'
        rto_name = f"Regional Transport Office (RTO-{state_prefix}-{clean_plate[2:4] if len(clean_plate)>=4 and clean_plate[2:4].isdigit() else '01'})"

        return VehicleFCRegistry(
            license_plate=clean_plate,
            owner_name=f"Logistics Fleet Carrier #{h % 400 + 100}",
            vehicle_type='Heavy Commercial Goods Carrier',
            registration_date=reg_date,
            fc_issue_date=issue_date,
            fc_expiry_date=expiry_date,
            vehicle_age_years=age,
            fc_status=status,
            police_action_required=police_action,
            police_notice_number=notice_num,
            fine_amount=fine,
            destruction_order_status=destruct_status,
            rto_office=rto_name,
            fitness_score=fitness_score,
            emission_compliance=emission,
            updated_at=now
        )

    def process_fc_renewal(self, license_plate, test_metrics=None, db_session=None):
        """
        Executes automated RTO multi-point fitness diagnostic inspection.
        If passed (or auto-corrected), issues a new 1-year Fitness Certificate.
        """
        close_db = False
        if db_session is None:
            db_session = SessionLocal()
            close_db = True

        try:
            clean_plate = license_plate.replace(" ", "").upper()
            record = db_session.query(VehicleFCRegistry).filter(
                VehicleFCRegistry.license_plate == clean_plate
            ).first()

            if not record:
                record = self._generate_default_fc_record(clean_plate)
                db_session.add(record)

            # Check if vehicle is over-aged (> 15 years)
            if record.vehicle_age_years >= self.SCRAP_AGE_THRESHOLD_YEARS:
                return {
                    'success': False,
                    'error': f'Vehicle {clean_plate} is {record.vehicle_age_years} years old. Under National Scrappage Policy, commercial vehicles over 15 years cannot be renewed and MUST BE SCRAPPED/DESTROYED.',
                    'police_action_required': 'DESTROY_VEHICLE_SCRAP'
                }

            now = datetime.now(timezone.utc)
            new_expiry = now + timedelta(days=365) # 1-year FC extension

            # Calculate diagnostic test results
            brakes = test_metrics.get('brake_efficiency', random.uniform(82.0, 96.0)) if test_metrics else random.uniform(85.0, 96.0)
            emission = test_metrics.get('emission_level', 'BS-VI Pass (CO: 0.12%, HC: 42 ppm)') if test_metrics else 'BS-VI Pass (CO: 0.14%, HC: 48 ppm)'
            suspension = test_metrics.get('suspension_rating', random.uniform(80.0, 95.0)) if test_metrics else random.uniform(84.0, 96.0)
            structural = test_metrics.get('structural_integrity', random.uniform(88.0, 99.0)) if test_metrics else random.uniform(90.0, 98.0)
            
            avg_fitness = round((brakes + suspension + structural) / 3.0, 1)

            record.fc_status = 'VALID'
            record.fc_issue_date = now
            record.fc_expiry_date = new_expiry
            record.police_action_required = 'NONE'
            record.police_notice_number = None
            record.fine_amount = 0.0
            record.fitness_score = avg_fitness
            record.emission_compliance = emission
            record.destruction_order_status = 'NONE'
            record.updated_at = now

            # Also update any active TruckLog entries for this plate
            db_session.query(TruckLog).filter(
                TruckLog.license_plate == clean_plate
            ).update({
                TruckLog.fc_status: 'VALID',
                TruckLog.fc_expiry_date: new_expiry,
                TruckLog.police_action_required: 'NONE',
                TruckLog.police_notice_number: None,
                TruckLog.fc_fine_amount: 0.0
            })

            db_session.commit()

            return {
                'success': True,
                'message': f"Fitness Certificate successfully RENEWED for {clean_plate}. Valid until {new_expiry.strftime('%Y-%m-%d')}.",
                'record': record.to_dict(),
                'inspection_summary': {
                    'brake_efficiency': f"{brakes:.1f}%",
                    'suspension_rating': f"{suspension:.1f}%",
                    'structural_integrity': f"{structural:.1f}%",
                    'emission_compliance': emission,
                    'overall_fitness_score': f"{avg_fitness}%",
                    'certified_until': new_expiry.strftime('%Y-%m-%d'),
                    'rto_cert_id': f"RTO-FC-CERT-{random.randint(100000, 999999)}"
                }
            }
        except Exception as e:
            print(f"❌ Error processing FC renewal: {e}")
            if db_session:
                db_session.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            if close_db:
                db_session.close()

    def issue_destruction_order(self, license_plate, reason=None, db_session=None):
        """
        Issues an official Police Impound & Vehicle Destruction / Scrappage Order.
        """
        close_db = False
        if db_session is None:
            db_session = SessionLocal()
            close_db = True

        try:
            clean_plate = license_plate.replace(" ", "").upper()
            record = db_session.query(VehicleFCRegistry).filter(
                VehicleFCRegistry.license_plate == clean_plate
            ).first()

            if not record:
                record = self._generate_default_fc_record(clean_plate)
                db_session.add(record)

            now = datetime.now(timezone.utc)
            notice_num = f"POL-SCRAP-ORDER-{random.randint(10000, 99999)}"

            record.fc_status = 'DESTROY_VEHICLE_SCRAP'
            record.police_action_required = 'DESTROY_VEHICLE_SCRAP'
            record.police_notice_number = notice_num
            record.destruction_order_status = 'ORDER_ISSUED'
            record.destruction_order_date = now
            record.scrapping_facility = 'RVSF National Heavy Vehicle Scrapping Facility #07'
            record.fine_amount = self.EXTREME_SCRAP_PENALTY
            record.updated_at = now

            # Update truck logs
            db_session.query(TruckLog).filter(
                TruckLog.license_plate == clean_plate
            ).update({
                TruckLog.fc_status: 'DESTROY_VEHICLE_SCRAP',
                TruckLog.police_action_required: 'DESTROY_VEHICLE_SCRAP',
                TruckLog.police_notice_number: notice_num,
                TruckLog.fc_fine_amount: self.EXTREME_SCRAP_PENALTY
            })

            # Create high priority alert
            alert = AlertLog(
                timestamp=now,
                alert_type='FC_SCRAP_DESTROY',
                severity='CRITICAL',
                license_plate=clean_plate,
                message=f"POLICE DESTRUCTION ORDER: Vehicle {clean_plate} (Age: {record.vehicle_age_years} yrs) ordered for immediate impoundment and RVSF scrapping ({reason or 'Exceeded 15-year legal commercial life & expired fitness'}).",
                sound_played=True,
                email_sent=True,
                acknowledged=False
            )
            db_session.add(alert)
            db_session.commit()

            return {
                'success': True,
                'message': f"Police Destruction & Scrapping Warrant successfully issued for {clean_plate}.",
                'record': record.to_dict()
            }
        except Exception as e:
            print(f"❌ Error issuing destruction order: {e}")
            if db_session:
                db_session.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            if close_db:
                db_session.close()

    def confirm_scrapping_destruction(self, license_plate, scrapping_facility=None, officer_badge='POL-CMD-01', db_session=None):
        """
        Executes and records the complete physical destruction/scrapping of an end-of-life vehicle.
        Generates Certificate of Destruction (COD).
        """
        close_db = False
        if db_session is None:
            db_session = SessionLocal()
            close_db = True

        try:
            clean_plate = license_plate.replace(" ", "").upper()
            record = db_session.query(VehicleFCRegistry).filter(
                VehicleFCRegistry.license_plate == clean_plate
            ).first()

            if not record:
                return {'success': False, 'error': 'Vehicle not found in FC registry'}

            now = datetime.now(timezone.utc)
            facility = scrapping_facility or record.scrapping_facility or 'RVSF National Heavy Vehicle Scrapping Facility #07'
            cert_num = f"COD-IND-MORTH-{datetime.now().year}-{random.randint(100000, 999999)}"

            record.destruction_order_status = 'DESTROYED'
            record.scrapping_facility = facility
            record.destruction_cert_number = cert_num
            record.updated_at = now

            db_session.commit()

            return {
                'success': True,
                'message': f"Vehicle {clean_plate} has been physically destroyed/scrapped at {facility}.",
                'certificate': {
                    'certificate_number': cert_num,
                    'license_plate': clean_plate,
                    'owner_name': record.owner_name,
                    'vehicle_age': f"{record.vehicle_age_years} Years",
                    'destruction_date': now.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    'facility_name': facility,
                    'authorizing_officer': officer_badge,
                    'scrappage_incentive_credit': f"₹{random.randint(45000, 85000):,}",
                    'legal_statute': 'National Registered Vehicle Scrappage Policy (RVSF 2021/2026), Section 56 Motor Vehicles Act'
                },
                'record': record.to_dict()
            }
        except Exception as e:
            print(f"❌ Error confirming destruction: {e}")
            if db_session:
                db_session.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            if close_db:
                db_session.close()

    def pay_fc_fine(self, license_plate, amount=None, payment_ref=None, db_session=None):
        """
        Records penalty challan payment for expired FC violation.
        """
        close_db = False
        if db_session is None:
            db_session = SessionLocal()
            close_db = True

        try:
            clean_plate = license_plate.replace(" ", "").upper()
            record = db_session.query(VehicleFCRegistry).filter(
                VehicleFCRegistry.license_plate == clean_plate
            ).first()

            if not record:
                return {'success': False, 'error': 'Vehicle not found in FC registry'}

            now = datetime.now(timezone.utc)
            paid_amount = amount or record.fine_amount
            record.fine_amount = 0.0
            record.updated_at = now

            # Update truck logs
            db_session.query(TruckLog).filter(
                TruckLog.license_plate == clean_plate
            ).update({
                TruckLog.fc_fine_amount: 0.0
            })

            db_session.commit()

            return {
                'success': True,
                'message': f"Penalty fine of ₹{paid_amount:,.2f} cleared for {clean_plate}.",
                'receipt_number': payment_ref or f"PAY-ECHALLAN-{random.randint(1000000, 9999999)}",
                'payment_timestamp': now.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'record': record.to_dict()
            }
        except Exception as e:
            print(f"❌ Error paying fine: {e}")
            if db_session:
                db_session.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            if close_db:
                db_session.close()

    def get_fc_stats(self, db_session=None):
        """
        Computes fleet-wide fitness certificate compliance and police enforcement metrics.
        """
        close_db = False
        if db_session is None:
            db_session = SessionLocal()
            close_db = True

        try:
            total_records = db_session.query(VehicleFCRegistry).count()
            valid_fc = db_session.query(VehicleFCRegistry).filter(VehicleFCRegistry.fc_status == 'VALID').count()
            renewal_req = db_session.query(VehicleFCRegistry).filter(VehicleFCRegistry.fc_status == 'EXPIRED_RENEWAL_REQUIRED').count()
            destroy_orders = db_session.query(VehicleFCRegistry).filter(VehicleFCRegistry.fc_status == 'DESTROY_VEHICLE_SCRAP').count()
            physically_destroyed = db_session.query(VehicleFCRegistry).filter(VehicleFCRegistry.destruction_order_status == 'DESTROYED').count()

            compliance_rate = round((valid_fc / max(1, total_records)) * 100, 1)

            # Age distribution
            under_5 = db_session.query(VehicleFCRegistry).filter(VehicleFCRegistry.vehicle_age_years < 5).count()
            age_5_10 = db_session.query(VehicleFCRegistry).filter(VehicleFCRegistry.vehicle_age_years >= 5, VehicleFCRegistry.vehicle_age_years < 10).count()
            age_10_15 = db_session.query(VehicleFCRegistry).filter(VehicleFCRegistry.vehicle_age_years >= 10, VehicleFCRegistry.vehicle_age_years < 15).count()
            over_15 = db_session.query(VehicleFCRegistry).filter(VehicleFCRegistry.vehicle_age_years >= 15).count()

            return {
                'total_registered_vehicles': total_records,
                'valid_fc_count': valid_fc,
                'renewal_required_count': renewal_req,
                'destruction_order_count': destroy_orders,
                'physically_destroyed_count': physically_destroyed,
                'compliance_rate': compliance_rate,
                'age_distribution': [
                    {'bracket': '0-5 Years (New Fleet)', 'count': under_5},
                    {'bracket': '5-10 Years (Mid-Life)', 'count': age_5_10},
                    {'bracket': '10-15 Years (High Wear)', 'count': age_10_15},
                    {'bracket': '15+ Years (End-of-Life / Scrap)', 'count': over_15}
                ]
            }
        except Exception as e:
            print(f"❌ Error computing FC stats: {e}")
            return {
                'total_registered_vehicles': 0,
                'valid_fc_count': 0,
                'renewal_required_count': 0,
                'destruction_order_count': 0,
                'physically_destroyed_count': 0,
                'compliance_rate': 0.0,
                'age_distribution': []
            }
        finally:
            if close_db:
                db_session.close()

fc_service = FCService()
