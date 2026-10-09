from datetime import datetime, timezone
from backend.database.models import TruckLog
from backend.database.db import SessionLocal

class LogisticsService:
    """
    Logistics & Cargo Analysis Service.
    Handles arrival/departure records, visit counting, and cargo turnaround dwell metrics.
    """
    def __init__(self):
        pass

    def record_truck_event(self, track_id, license_plate, speed, speed_limit, is_overspeed,
                           truck_type, color, cargo_attributes, camera_id='CAM-HIGHWAY-01',
                           snapshot_path=None, fc_status='VALID', fc_expiry_date=None,
                           vehicle_age_years=4, police_action_required='NONE',
                           police_notice_number=None, fc_fine_amount=0.0, db_session=None):
        """
        Logs a truck detection event and updates visit count and FC enforcement metadata.
        """
        close_db = False
        if db_session is None:
            db_session = SessionLocal()
            close_db = True

        try:
            # 1. Compute visit count for this plate
            past_visits = db_session.query(TruckLog).filter(
                TruckLog.license_plate == license_plate
            ).count()
            
            visit_count = past_visits + 1
            now = datetime.now(timezone.utc)

            # 2. Create new TruckLog entry
            truck_log = TruckLog(
                track_id=track_id,
                license_plate=license_plate,
                speed=speed,
                speed_limit=speed_limit,
                is_overspeed=is_overspeed,
                truck_type=truck_type,
                color=color,
                cargo_attributes=cargo_attributes,
                arrival_time=now,
                visit_count=visit_count,
                fc_status=fc_status,
                fc_expiry_date=fc_expiry_date,
                vehicle_age_years=vehicle_age_years,
                police_action_required=police_action_required,
                police_notice_number=police_notice_number,
                fc_fine_amount=fc_fine_amount,
                camera_id=camera_id,
                snapshot_path=snapshot_path,
                created_at=now
            )
            db_session.add(truck_log)
            db_session.commit()
            return truck_log.to_dict()
        except Exception as e:
            print(f"❌ Error logging truck event: {e}")
            if db_session:
                db_session.rollback()
            return None
        finally:
            if close_db:
                db_session.close()


    def record_departure(self, license_plate, db_session=None):
        """
        Updates the most recent truck log with departure timestamp.
        """
        close_db = False
        if db_session is None:
            db_session = SessionLocal()
            close_db = True

        try:
            latest_log = db_session.query(TruckLog).filter(
                TruckLog.license_plate == license_plate,
                TruckLog.departure_time == None
            ).order_by(TruckLog.arrival_time.desc()).first()

            if latest_log:
                latest_log.departure_time = datetime.now(timezone.utc)
                db_session.commit()
                return latest_log.to_dict()
            return None
        except Exception as e:
            print(f"❌ Error recording departure: {e}")
            if db_session:
                db_session.rollback()
            return None
        finally:
            if close_db:
                db_session.close()

logistics_service = LogisticsService()
