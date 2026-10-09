import os
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from backend.config import Config
from backend.database.models import Base, TruckLog, AlertLog, Blocklist, SystemConfig, User, VehicleFCRegistry

# Ensure data directory exists
os.makedirs(os.path.dirname(Config.DEFAULT_SQLITE_PATH), exist_ok=True)
os.makedirs(Config.SNAPSHOT_DIR, exist_ok=True)
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    echo=False,
    pool_pre_ping=True
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _migrate_tables():
    """Ensures newly added columns exist in existing database tables."""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'truck_logs' in tables:
            columns = [c['name'] for c in inspector.get_columns('truck_logs')]
            with engine.connect() as conn:
                if 'fc_status' not in columns:
                    conn.execute(text("ALTER TABLE truck_logs ADD COLUMN fc_status VARCHAR(50) DEFAULT 'VALID'"))
                if 'fc_expiry_date' not in columns:
                    conn.execute(text("ALTER TABLE truck_logs ADD COLUMN fc_expiry_date DATETIME"))
                if 'vehicle_age_years' not in columns:
                    conn.execute(text("ALTER TABLE truck_logs ADD COLUMN vehicle_age_years INTEGER DEFAULT 4"))
                if 'police_action_required' not in columns:
                    conn.execute(text("ALTER TABLE truck_logs ADD COLUMN police_action_required VARCHAR(50) DEFAULT 'NONE'"))
                if 'police_notice_number' not in columns:
                    conn.execute(text("ALTER TABLE truck_logs ADD COLUMN police_notice_number VARCHAR(50)"))
                if 'fc_fine_amount' not in columns:
                    conn.execute(text("ALTER TABLE truck_logs ADD COLUMN fc_fine_amount FLOAT DEFAULT 0.0"))
                conn.commit()
    except Exception as e:
        print(f"⚠️ Migration notice: {e}")

def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_tables()
    seed_initial_data()


def refresh_image_database(count=160):
    """
    Regenerates/Updates the surveillance database with `count` (100-250)
    high-definition CCTV snapshot images, cropped license plates, and YOLO annotations.
    """
    from backend.ai_engine.image_dataset_generator import dataset_generator
    from backend.services.fc_service import fc_service
    
    db = SessionLocal()
    try:
        print(f"[DATASET] Refreshing and generating {count} heavy vehicle image records for surveillance database...")
        
        # Clear existing truck logs and alerts to ensure complete image alignment
        db.query(AlertLog).delete()
        db.query(TruckLog).delete()
        db.commit()
        
        # Generate 150-200 realistic CCTV snapshot images
        records = dataset_generator.generate_dataset(target_count=count)
        
        visit_tracker = {}
        for r in records:
            plate = r['license_plate']
            visit_tracker[plate] = visit_tracker.get(plate, 0) + 1
            
            arrival = r['timestamp']
            departure = arrival + timedelta(minutes=random.randint(20, 180)) if random.random() > 0.2 else None
            
            # Lookup FC verification details
            fc_data = fc_service.verify_fc_status(plate, db_session=db)
            fc_status = fc_data.get('fc_status', 'VALID')
            vehicle_age = fc_data.get('vehicle_age_years', 4)
            police_action = fc_data.get('police_action_required', 'NONE')
            notice_num = fc_data.get('police_notice_number', None)
            fine_amount = fc_data.get('fine_amount', 0.0)
            fc_exp_iso = fc_data.get('fc_expiry_date')
            fc_expiry = datetime.fromisoformat(fc_exp_iso) if fc_exp_iso else None

            log = TruckLog(
                track_id=r['track_id'],
                license_plate=plate,
                speed=r['speed'],
                speed_limit=60.0,
                is_overspeed=r['is_overspeed'],
                truck_type=r['truck_type'],
                color=r['color'],
                cargo_attributes=r['cargo_attributes'],
                arrival_time=arrival,
                departure_time=departure,
                visit_count=visit_tracker[plate],
                fc_status=fc_status,
                fc_expiry_date=fc_expiry,
                vehicle_age_years=vehicle_age,
                police_action_required=police_action,
                police_notice_number=notice_num,
                fc_fine_amount=fine_amount,
                camera_id=r['camera_id'],
                snapshot_path=r['snapshot_filename'],
                created_at=arrival
            )
            db.add(log)
            
            # Add AlertLog for Blocklist, Overspeed, and FC Violations/Destruction Orders
            if r['is_blocklisted']:
                db.add(AlertLog(
                    timestamp=arrival,
                    alert_type='BLOCKLIST_MATCH',
                    severity='CRITICAL',
                    track_id=r['track_id'],
                    license_plate=plate,
                    speed=r['speed'],
                    message=f"CRITICAL WATCHLIST HIT: Vehicle {plate} matched active alert registry.",
                    sound_played=True,
                    email_sent=True,
                    acknowledged=random.random() > 0.4,
                    created_at=arrival
                ))
            elif police_action == 'DESTROY_VEHICLE_SCRAP':
                db.add(AlertLog(
                    timestamp=arrival,
                    alert_type='FC_SCRAP_DESTROY',
                    severity='CRITICAL',
                    track_id=r['track_id'],
                    license_plate=plate,
                    speed=r['speed'],
                    message=f"POLICE DESTRUCTION WARRANT: Vehicle {plate} is {vehicle_age} yrs old with expired FC. Immediate impound & RVSF scrapping ordered (Notice #{notice_num}).",
                    sound_played=True,
                    email_sent=True,
                    acknowledged=random.random() > 0.4,
                    created_at=arrival
                ))
            elif police_action == 'FC_RENEWAL_PROCESS':
                db.add(AlertLog(
                    timestamp=arrival,
                    alert_type='FC_EXPIRED_RENEWAL',
                    severity='HIGH',
                    track_id=r['track_id'],
                    license_plate=plate,
                    speed=r['speed'],
                    message=f"FITNESS EXPIRED: Vehicle {plate} (Age: {vehicle_age} yrs) operating without valid FC. Mandatory FC renewal process & fine ₹5,000 required (Challan #{notice_num}).",
                    sound_played=True,
                    email_sent=False,
                    acknowledged=random.random() > 0.3,
                    created_at=arrival
                ))
            elif r['is_overspeed']:
                db.add(AlertLog(
                    timestamp=arrival,
                    alert_type='OVERSPEED',
                    severity='HIGH' if r['speed'] > 75.0 else 'MEDIUM',
                    track_id=r['track_id'],
                    license_plate=plate,
                    speed=r['speed'],
                    message=f"OVERSPEED VIOLATION: {r['track_id']} ({plate}) detected at {r['speed']} km/h (Limit: 60 km/h).",
                    sound_played=True,
                    email_sent=r['speed'] > 75.0,
                    acknowledged=random.random() > 0.3,
                    created_at=arrival
                ))
                
        db.commit()
        print(f"[OK] Successfully seeded database with {len(records)} image-backed vehicle dossiers.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during image database refresh: {e}")
    finally:
        db.close()

def seed_initial_data():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Seed default users if users table is empty
        if db.query(User).first() is None:
            admin_user = User(
                email='admin@visionhaul.ai',
                password='admin',
                name='Commander Alexander Vance',
                role='Admin',
                badge_id='SEC-CMD-01',
                department='National Heavy Transport Security Command',
                clearance='Level 5 (Full Command & Calibration)'
            )
            manager_user = User(
                email='manager@visionhaul.ai',
                password='manager',
                name='Director Sarah Jenkins',
                role='Manager',
                badge_id='LOG-MGR-04',
                department='Port & Highway Logistics Operations',
                clearance='Level 3 (Surveillance & Logistics)'
            )
            db.add(admin_user)
            db.add(manager_user)
            db.commit()

        # Seed System Configs if empty
        if db.query(SystemConfig).first() is None:
            default_configs = [
                SystemConfig(key='speed_limit', value='60.0', description='Max allowed speed in km/h'),
                SystemConfig(key='sound_alert_enabled', value='true', description='Play audio siren on high severity alert'),
                SystemConfig(key='email_alert_enabled', value='true', description='Send SMTP emails on alerts'),
                SystemConfig(key='alert_recipient_email', value='security.director@portlogistics.com', description='Authorized email recipient'),
                SystemConfig(key='camera_source', value='SIMULATED', description='Camera source: SIMULATED, WEBCAM, or VIDEO_FILE'),
                SystemConfig(key='homography_calibration', value='18.5', description='Pixels to meters calibration factor'),
                SystemConfig(key='fc_scrappage_threshold_years', value='15', description='Commercial vehicle age threshold in years for mandatory scrapping/destruction')
            ]
            for cfg in default_configs:
                db.add(cfg)
            db.commit()
            
        # Seed Blocklist if empty
        if db.query(Blocklist).first() is None:
            blocklist_entries = [
                Blocklist(license_plate='TN38AB1234', reason='Reported Stolen Trailer - Police Alert #CR-8821', severity='CRITICAL', added_by='National Police Registry'),
                Blocklist(license_plate='KA01MJ9944', reason='Suspected Smuggling / Unmanifested Cargo', severity='CRITICAL', added_by='Port Customs Enforcement'),
                Blocklist(license_plate='MH12PK4321', reason='Revoked Commercial Carrier Safety Permit', severity='HIGH', added_by='Department of Transportation'),
                Blocklist(license_plate='DL01TX8822', reason='Outstanding Environmental & Hazardous Cargo Fine', severity='HIGH', added_by='Environmental Agency'),
                Blocklist(license_plate='GJ04BC5566', reason='Counterfeit Fuel Tanker Registration', severity='CRITICAL', added_by='State Border Patrol')
            ]
            for b in blocklist_entries:
                db.add(b)
            db.commit()

        # Seed Vehicle FC Registry if empty
        if db.query(VehicleFCRegistry).first() is None:
            fc_entries = [
                # 1. Over-aged End-of-Life Vehicles (>15 yrs) -> MUST BE DESTROYED / SCRAPPED
                VehicleFCRegistry(
                    license_plate='TN38AB1234',
                    owner_name='Southern Heavy Freightlines Ltd.',
                    vehicle_type='Tata Signa Heavy Multi-Axle Goods Carrier',
                    registration_date=now - timedelta(days=17*365 + 120),
                    fc_issue_date=now - timedelta(days=480),
                    fc_expiry_date=now - timedelta(days=115),
                    vehicle_age_years=17,
                    fc_status='DESTROY_VEHICLE_SCRAP',
                    police_action_required='DESTROY_VEHICLE_SCRAP',
                    police_notice_number='POL-SCRAP-2026-0812',
                    fine_amount=25000.0,
                    destruction_order_status='ORDER_ISSUED',
                    destruction_order_date=now - timedelta(days=12),
                    scrapping_facility='RVSF National Heavy Vehicle Scrapping Facility #07',
                    rto_office='Regional Transport Office (RTO-TN-38 Coimbatore)',
                    fitness_score=36.5,
                    emission_compliance='BS-III Failed (High PM2.5 & Hydrocarbon Emission)'
                ),
                VehicleFCRegistry(
                    license_plate='KA01MJ9944',
                    owner_name='Deccan Quarry Mining Transport',
                    vehicle_type='Ashok Leyland Captain Tipper Lorry',
                    registration_date=now - timedelta(days=16*365 + 45),
                    fc_issue_date=now - timedelta(days=620),
                    fc_expiry_date=now - timedelta(days=255),
                    vehicle_age_years=16,
                    fc_status='DESTROY_VEHICLE_SCRAP',
                    police_action_required='DESTROY_VEHICLE_SCRAP',
                    police_notice_number='POL-SCRAP-2026-1144',
                    fine_amount=25000.0,
                    destruction_order_status='ORDER_ISSUED',
                    destruction_order_date=now - timedelta(days=28),
                    scrapping_facility='RVSF Karnataka State Eco-Scrap Yard #02',
                    rto_office='Regional Transport Office (RTO-KA-01 Bangalore Central)',
                    fitness_score=41.2,
                    emission_compliance='BS-III Failed (Structural Rust & Brake Failure)'
                ),
                VehicleFCRegistry(
                    license_plate='GJ04BC5566',
                    owner_name='Western Petroleum Haulers',
                    vehicle_type='Tata 1613 Goods Carrier Lorry',
                    registration_date=now - timedelta(days=18*365 + 90),
                    fc_issue_date=now - timedelta(days=700),
                    fc_expiry_date=now - timedelta(days=335),
                    vehicle_age_years=18,
                    fc_status='DESTROY_VEHICLE_SCRAP',
                    police_action_required='DESTROY_VEHICLE_SCRAP',
                    police_notice_number='POL-SCRAP-2026-9044',
                    fine_amount=25000.0,
                    destruction_order_status='IMPOUNDED',
                    destruction_order_date=now - timedelta(days=4),
                    scrapping_facility='RVSF Gujarat Green Scrapping Center #01',
                    rto_office='Regional Transport Office (RTO-GJ-04 Bhavnagar)',
                    fitness_score=29.0,
                    emission_compliance='BS-II Failed (Critical Chassis Fatigue)'
                ),
                VehicleFCRegistry(
                    license_plate='AP02KL8877',
                    owner_name='Krishna River Sand Logistics',
                    vehicle_type='Heavy Duty Tipper Truck',
                    registration_date=now - timedelta(days=19*365 + 10),
                    fc_issue_date=now - timedelta(days=820),
                    fc_expiry_date=now - timedelta(days=455),
                    vehicle_age_years=19,
                    fc_status='DESTROY_VEHICLE_SCRAP',
                    police_action_required='DESTROY_VEHICLE_SCRAP',
                    police_notice_number='POL-SCRAP-2026-3399',
                    fine_amount=25000.0,
                    destruction_order_status='DESTROYED',
                    destruction_order_date=now - timedelta(days=40),
                    scrapping_facility='RVSF Andhra Coastal Scrappage Hub',
                    destruction_cert_number='COD-MORTH-2026-AP-9921',
                    rto_office='Regional Transport Office (RTO-AP-02 Anantapur)',
                    fitness_score=22.0,
                    emission_compliance='BS-II Scrapped & Destroyed'
                ),

                # 2. Expired FC under 15 years old -> CAN DO FC RENEWAL PROCESS
                VehicleFCRegistry(
                    license_plate='MH12PK4321',
                    owner_name='Sahyadri Inter-State Petroleum',
                    vehicle_type='Bharat Petroleum Fuel Tanker (Hazmat)',
                    registration_date=now - timedelta(days=7*365 + 30),
                    fc_issue_date=now - timedelta(days=390),
                    fc_expiry_date=now - timedelta(days=25),
                    vehicle_age_years=7,
                    fc_status='EXPIRED_RENEWAL_REQUIRED',
                    police_action_required='FC_RENEWAL_PROCESS',
                    police_notice_number='POL-FC-2026-4411',
                    fine_amount=5000.0,
                    destruction_order_status='NONE',
                    rto_office='Regional Transport Office (RTO-MH-12 Pune)',
                    fitness_score=68.4,
                    emission_compliance='BS-IV Conditional (Requires Annual Re-Test)'
                ),
                VehicleFCRegistry(
                    license_plate='DL01TX8822',
                    owner_name='Capital Express Cargo Carriers',
                    vehicle_type='BharatBenz ISO Container Hauler',
                    registration_date=now - timedelta(days=6*365 + 80),
                    fc_issue_date=now - timedelta(days=410),
                    fc_expiry_date=now - timedelta(days=45),
                    vehicle_age_years=6,
                    fc_status='EXPIRED_RENEWAL_REQUIRED',
                    police_action_required='FC_RENEWAL_PROCESS',
                    police_notice_number='POL-FC-2026-8822',
                    fine_amount=5000.0,
                    destruction_order_status='NONE',
                    rto_office='Regional Transport Office (RTO-DL-01 Mall Road)',
                    fitness_score=71.0,
                    emission_compliance='BS-IV Conditional (Brake Retest Pending)'
                ),
                VehicleFCRegistry(
                    license_plate='WB19GH2233',
                    owner_name='Eastern Corridor Petrochem Haulage',
                    vehicle_type='Bulk Liquid Petroleum Tanker',
                    registration_date=now - timedelta(days=9*365 + 20),
                    fc_issue_date=now - timedelta(days=400),
                    fc_expiry_date=now - timedelta(days=35),
                    vehicle_age_years=9,
                    fc_status='EXPIRED_RENEWAL_REQUIRED',
                    police_action_required='FC_RENEWAL_PROCESS',
                    police_notice_number='POL-FC-2026-2233',
                    fine_amount=5000.0,
                    destruction_order_status='NONE',
                    rto_office='Regional Transport Office (RTO-WB-19 Alipore)',
                    fitness_score=64.8,
                    emission_compliance='BS-IV Expired (Emission Retest Required)'
                ),

                # 3. Valid FC -> COMPLIANT FLEET
                VehicleFCRegistry(
                    license_plate='TN48AJ8168',
                    owner_name='Highway Express Passenger & Commercial Fleet',
                    vehicle_type='Hyundai White Passenger Sedan / Utility Vehicle',
                    registration_date=now - timedelta(days=3*365 + 40),
                    fc_issue_date=now - timedelta(days=90),
                    fc_expiry_date=now + timedelta(days=275),
                    vehicle_age_years=3,
                    fc_status='VALID',
                    police_action_required='NONE',
                    police_notice_number=None,
                    fine_amount=0.0,
                    destruction_order_status='NONE',
                    rto_office='Regional Transport Office (RTO-TN-48 Srirangam / Tiruchirappalli)',
                    fitness_score=95.0,
                    emission_compliance='BS-VI Compliant'
                ),
                VehicleFCRegistry(
                    license_plate='TN45Z4005',
                    owner_name='Velmani Transports Heavy Commercial Logistics',
                    vehicle_type='Heavy Commercial Goods Carrier / Freight Truck',
                    registration_date=now - timedelta(days=8*365 + 60),
                    fc_issue_date=now - timedelta(days=420),
                    fc_expiry_date=now - timedelta(days=55),
                    vehicle_age_years=8,
                    fc_status='EXPIRED_RENEWAL_REQUIRED',
                    police_action_required='FC_RENEWAL_PROCESS',
                    police_notice_number='POL-FC-2026-4005',
                    fine_amount=5000.0,
                    destruction_order_status='NONE',
                    rto_office='Regional Transport Office (RTO-TN-45 Tiruchirappalli)',
                    fitness_score=72.0,
                    emission_compliance='BS-IV Conditional (Requires Annual Re-Test)'
                ),
                VehicleFCRegistry(
                    license_plate='TN09AZ7788',
                    owner_name='Coromandel FastAgri Cold Chain',
                    vehicle_type='Refrigerated Container Carrier',
                    registration_date=now - timedelta(days=2*365),
                    fc_issue_date=now - timedelta(days=60),
                    fc_expiry_date=now + timedelta(days=305),
                    vehicle_age_years=2,
                    fc_status='VALID',
                    police_action_required='NONE',
                    police_notice_number=None,
                    fine_amount=0.0,
                    destruction_order_status='NONE',
                    rto_office='Regional Transport Office (RTO-TN-09 Chennai Central)',
                    fitness_score=96.5,
                    emission_compliance='BS-VI Compliant'
                ),
                VehicleFCRegistry(
                    license_plate='TS08EE9911',
                    owner_name='Telangana Multi-Modal Logistics',
                    vehicle_type='Container Carrier Prime Mover',
                    registration_date=now - timedelta(days=3*365),
                    fc_issue_date=now - timedelta(days=110),
                    fc_expiry_date=now + timedelta(days=255),
                    vehicle_age_years=3,
                    fc_status='VALID',
                    police_action_required='NONE',
                    police_notice_number=None,
                    fine_amount=0.0,
                    destruction_order_status='NONE',
                    rto_office='Regional Transport Office (RTO-TS-08 Medchal)',
                    fitness_score=94.0,
                    emission_compliance='BS-VI Compliant'
                ),
                VehicleFCRegistry(
                    license_plate='HR26BR4001',
                    owner_name='Northern Heavy Haulers Pvt Ltd',
                    vehicle_type='Flatbed Heavy Machinery Carrier',
                    registration_date=now - timedelta(days=4*365),
                    fc_issue_date=now - timedelta(days=90),
                    fc_expiry_date=now + timedelta(days=275),
                    vehicle_age_years=4,
                    fc_status='VALID',
                    police_action_required='NONE',
                    police_notice_number=None,
                    fine_amount=0.0,
                    destruction_order_status='NONE',
                    rto_office='Regional Transport Office (RTO-HR-26 Gurgaon North)',
                    fitness_score=92.5,
                    emission_compliance='BS-VI Compliant'
                ),
                VehicleFCRegistry(
                    license_plate='KL07QR3344',
                    owner_name='Kochi Marine Port Forwarders',
                    vehicle_type='Heavy Container Hauler',
                    registration_date=now - timedelta(days=3*365 + 140),
                    fc_issue_date=now - timedelta(days=120),
                    fc_expiry_date=now + timedelta(days=245),
                    vehicle_age_years=3,
                    fc_status='VALID',
                    police_action_required='NONE',
                    police_notice_number=None,
                    fine_amount=0.0,
                    destruction_order_status='NONE',
                    rto_office='Regional Transport Office (RTO-KL-07 Ernakulam)',
                    fitness_score=95.0,
                    emission_compliance='BS-VI Compliant'
                )
            ]
            for fc in fc_entries:
                db.add(fc)
            db.commit()

        # Ensure video vehicle plates exist in FC registry
        for p_test in ['TN48AJ8168', 'TN45Z4005']:
            if not db.query(VehicleFCRegistry).filter(VehicleFCRegistry.license_plate == p_test).first():
                if p_test == 'TN48AJ8168':
                    db.add(VehicleFCRegistry(
                        license_plate='TN48AJ8168',
                        owner_name='Highway Express Passenger & Commercial Fleet',
                        vehicle_type='Hyundai White Passenger Sedan / Utility Vehicle',
                        registration_date=now - timedelta(days=3*365 + 40),
                        fc_issue_date=now - timedelta(days=90),
                        fc_expiry_date=now + timedelta(days=275),
                        vehicle_age_years=3,
                        fc_status='VALID',
                        police_action_required='NONE',
                        police_notice_number=None,
                        fine_amount=0.0,
                        destruction_order_status='NONE',
                        rto_office='Regional Transport Office (RTO-TN-48 Srirangam / Tiruchirappalli)',
                        fitness_score=95.0,
                        emission_compliance='BS-VI Compliant'
                    ))
                elif p_test == 'TN45Z4005':
                    db.add(VehicleFCRegistry(
                        license_plate='TN45Z4005',
                        owner_name='Velmani Transports Heavy Commercial Logistics',
                        vehicle_type='Heavy Commercial Goods Carrier / Freight Truck',
                        registration_date=now - timedelta(days=8*365 + 60),
                        fc_issue_date=now - timedelta(days=420),
                        fc_expiry_date=now - timedelta(days=55),
                        vehicle_age_years=8,
                        fc_status='EXPIRED_RENEWAL_REQUIRED',
                        police_action_required='FC_RENEWAL_PROCESS',
                        police_notice_number='POL-FC-2026-4005',
                        fine_amount=5000.0,
                        destruction_order_status='NONE',
                        rto_office='Regional Transport Office (RTO-TN-45 Tiruchirappalli)',
                        fitness_score=72.0,
                        emission_compliance='BS-IV Conditional (Requires Annual Re-Test)'
                    ))
        db.commit()

        # Check if truck logs exist with valid image snapshots
        truck_count = db.query(TruckLog).count()
        truck_with_img = db.query(TruckLog).filter(TruckLog.snapshot_path != None).count()
        
        # If no logs or logs have no images, populate 160 image-based vehicle records
        if truck_count == 0 or truck_with_img < 100:
            print("[INFO] Seeding 160 image-backed surveillance vehicle records...")
            refresh_image_database(count=160)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding database: {e}")
    finally:
        db.close()

