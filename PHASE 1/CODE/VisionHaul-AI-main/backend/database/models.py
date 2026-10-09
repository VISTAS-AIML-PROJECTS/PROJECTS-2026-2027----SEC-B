from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TruckLog(Base):
    __tablename__ = 'truck_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(String(50), nullable=False, index=True)          # e.g., TRK001
    license_plate = Column(String(50), nullable=False, index=True)     # e.g., TN38AB1234
    speed = Column(Float, nullable=False)                              # e.g., 72.4 km/h
    speed_limit = Column(Float, default=60.0)                          # e.g., 60.0 km/h
    is_overspeed = Column(Boolean, default=False)
    
    # MTL-ViT Classifications
    truck_type = Column(String(100), default='Container Carrier')      # Flatbed, Tanker, Dump, etc.
    color = Column(String(50), default='White')                        # White, Yellow, Blue, etc.
    cargo_attributes = Column(String(200), default='Sealed Container') # Loaded, Empty Bed, Hazmat, etc.
    
    # Logistics & Dwell Analytics
    arrival_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    departure_time = Column(DateTime, nullable=True)
    visit_count = Column(Integer, default=1)                           # Count of visits for this plate
    
    # Fitness Certificate (FC) & Police Enforcement
    fc_status = Column(String(50), default='VALID')                   # 'VALID', 'EXPIRED_RENEWAL_REQUIRED', 'DESTROY_VEHICLE_SCRAP'
    fc_expiry_date = Column(DateTime, nullable=True)
    vehicle_age_years = Column(Integer, default=4)
    police_action_required = Column(String(50), default='NONE')        # 'NONE', 'FC_RENEWAL_PROCESS', 'DESTROY_VEHICLE_SCRAP'
    police_notice_number = Column(String(50), nullable=True)
    fc_fine_amount = Column(Float, default=0.0)

    # Camera / Feed Metadata
    camera_id = Column(String(50), default='CAM-HIGHWAY-01')
    snapshot_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'track_id': self.track_id,
            'license_plate': self.license_plate,
            'speed': round(self.speed, 1),
            'speed_limit': self.speed_limit,
            'is_overspeed': self.is_overspeed,
            'truck_type': self.truck_type,
            'color': self.color,
            'cargo_attributes': self.cargo_attributes,
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None,
            'departure_time': self.departure_time.isoformat() if self.departure_time else None,
            'visit_count': self.visit_count,
            'fc_status': self.fc_status,
            'fc_expiry_date': self.fc_expiry_date.isoformat() if self.fc_expiry_date else None,
            'vehicle_age_years': self.vehicle_age_years,
            'police_action_required': self.police_action_required,
            'police_notice_number': self.police_notice_number,
            'fc_fine_amount': self.fc_fine_amount,
            'camera_id': self.camera_id,
            'snapshot_path': self.snapshot_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class VehicleFCRegistry(Base):
    """
    RTO & Police National Vehicle Fitness Certificate (FC) Registry.
    Tracks vehicle age, fitness testing validity, emission compliance,
    mandatory FC renewals, and Police Vehicle Scrapping / Destruction Orders.
    """
    __tablename__ = 'vehicle_fc_registry'

    id = Column(Integer, primary_key=True, autoincrement=True)
    license_plate = Column(String(50), unique=True, nullable=False, index=True) # e.g. TN38AB1234
    owner_name = Column(String(120), default='Commercial Logistics Operator')
    vehicle_type = Column(String(100), default='Heavy Goods Vehicle')
    registration_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    fc_issue_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    fc_expiry_date = Column(DateTime, nullable=False)
    vehicle_age_years = Column(Integer, default=5)
    
    # FC Compliance State: 'VALID', 'EXPIRED_RENEWAL_REQUIRED', 'DESTROY_VEHICLE_SCRAP'
    fc_status = Column(String(50), default='VALID', index=True)
    
    # Police Enforcement Action: 'NONE', 'FC_RENEWAL_PROCESS', 'DESTROY_VEHICLE_SCRAP'
    police_action_required = Column(String(50), default='NONE')
    police_notice_number = Column(String(50), nullable=True)          # e.g., POL-FC-2026-9812
    fine_amount = Column(Float, default=0.0)                          # Outstanding penalty challan
    
    # Scrappage / Destruction lifecycle: 'NONE', 'ORDER_ISSUED', 'IMPOUNDED', 'DESTROYED'
    destruction_order_status = Column(String(50), default='NONE')
    destruction_order_date = Column(DateTime, nullable=True)
    scrapping_facility = Column(String(150), nullable=True)           # e.g. 'RVSF National Eco-Scrap Center #04'
    destruction_cert_number = Column(String(100), nullable=True)      # e.g. 'COD-2026-NH44-0899'
    
    rto_office = Column(String(100), default='Regional Transport Office (RTO-TN-38)')
    fitness_score = Column(Float, default=85.0)                       # Diagnostic score 0-100%
    emission_compliance = Column(String(50), default='BS-VI Compliant')
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'license_plate': self.license_plate,
            'owner_name': self.owner_name,
            'vehicle_type': self.vehicle_type,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'fc_issue_date': self.fc_issue_date.isoformat() if self.fc_issue_date else None,
            'fc_expiry_date': self.fc_expiry_date.isoformat() if self.fc_expiry_date else None,
            'vehicle_age_years': self.vehicle_age_years,
            'fc_status': self.fc_status,
            'police_action_required': self.police_action_required,
            'police_notice_number': self.police_notice_number,
            'fine_amount': self.fine_amount,
            'destruction_order_status': self.destruction_order_status,
            'destruction_order_date': self.destruction_order_date.isoformat() if self.destruction_order_date else None,
            'scrapping_facility': self.scrapping_facility,
            'destruction_cert_number': self.destruction_cert_number,
            'rto_office': self.rto_office,
            'fitness_score': self.fitness_score,
            'emission_compliance': self.emission_compliance,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AlertLog(Base):
    __tablename__ = 'alert_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    alert_type = Column(String(50), nullable=False)                    # OVERSPEED, BLOCKLIST_MATCH, FC_EXPIRED_RENEWAL, FC_SCRAP_DESTROY
    severity = Column(String(20), default='HIGH')                      # LOW, MEDIUM, HIGH, CRITICAL
    track_id = Column(String(50), nullable=True)
    license_plate = Column(String(50), nullable=True)
    speed = Column(Float, nullable=True)
    message = Column(Text, nullable=False)
    sound_played = Column(Boolean, default=True)
    email_sent = Column(Boolean, default=False)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'track_id': self.track_id,
            'license_plate': self.license_plate,
            'speed': round(self.speed, 1) if self.speed is not None else None,
            'message': self.message,
            'sound_played': self.sound_played,
            'email_sent': self.email_sent,
            'acknowledged': self.acknowledged,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Blocklist(Base):
    __tablename__ = 'blocklist'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    license_plate = Column(String(50), unique=True, nullable=False, index=True)
    reason = Column(String(255), nullable=False)                       # Stolen vehicle, Expired Permit, Suspicious
    severity = Column(String(20), default='CRITICAL')                  # HIGH, CRITICAL
    added_by = Column(String(100), default='Security Supervisor')
    date_added = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'license_plate': self.license_plate,
            'reason': self.reason,
            'severity': self.severity,
            'added_by': self.added_by,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'active': self.active
        }


class SystemConfig(Base):
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default='Manager')         # 'Admin' or 'Manager'
    badge_id = Column(String(50), nullable=False, default='SEC-001')
    department = Column(String(100), default='Port & Highway Logistics Security')
    clearance = Column(String(100), default='Level 3 (Surveillance & Logistics)')
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'badge_id': self.badge_id,
            'department': self.department,
            'clearance': self.clearance,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


