from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from sqlalchemy import desc, or_
from backend.database.db import SessionLocal
from backend.database.models import VehicleFCRegistry, TruckLog
from backend.services.fc_service import fc_service

fc_bp = Blueprint('fc_bp', __name__)

@fc_bp.route('/records', methods=['GET'])
def get_fc_records():
    """
    Paginated search and filter for Vehicle Fitness Certificate Registry.
    Query params: page, limit, search, fc_status, police_action
    """
    db = SessionLocal()
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '').strip()
        fc_status = request.args.get('fc_status', '').strip().upper()
        police_action = request.args.get('police_action', '').strip().upper()

        query = db.query(VehicleFCRegistry)

        if search:
            query = query.filter(
                or_(
                    VehicleFCRegistry.license_plate.ilike(f"%{search}%"),
                    VehicleFCRegistry.owner_name.ilike(f"%{search}%"),
                    VehicleFCRegistry.police_notice_number.ilike(f"%{search}%"),
                    VehicleFCRegistry.rto_office.ilike(f"%{search}%")
                )
            )

        if fc_status:
            query = query.filter(VehicleFCRegistry.fc_status == fc_status)

        if police_action:
            query = query.filter(VehicleFCRegistry.police_action_required == police_action)

        total = query.count()
        records = query.order_by(desc(VehicleFCRegistry.updated_at)).offset((page - 1) * limit).limit(limit).all()

        return jsonify({
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit,
            'records': [r.to_dict() for r in records]
        })
    finally:
        db.close()


@fc_bp.route('/verify/<string:license_plate>', methods=['GET'])
def verify_plate_fc(license_plate):
    """
    Real-time lookup and verification of a license plate's FC status.
    """
    db = SessionLocal()
    try:
        res = fc_service.verify_fc_status(license_plate, db_session=db)
        return jsonify(res)
    finally:
        db.close()


@fc_bp.route('/stats', methods=['GET'])
def get_fc_stats():
    """
    Fleet-wide FC compliance, scrappage, and police enforcement statistics.
    """
    db = SessionLocal()
    try:
        stats = fc_service.get_fc_stats(db_session=db)
        return jsonify(stats)
    finally:
        db.close()


@fc_bp.route('/renew', methods=['POST'])
def renew_fitness_certificate():
    """
    Submits vehicle for automated multi-point RTO fitness diagnostic and issues renewed FC.
    """
    data = request.json or {}
    plate = data.get('license_plate', '').strip()
    if not plate:
        return jsonify({'error': 'License plate is required'}), 400

    test_metrics = data.get('test_metrics', None)
    
    db = SessionLocal()
    try:
        result = fc_service.process_fc_renewal(plate, test_metrics=test_metrics, db_session=db)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    finally:
        db.close()


@fc_bp.route('/destruction-order', methods=['POST'])
def issue_destruction_order():
    """
    Issues a Police Impound & Vehicle Destruction / Scrapping Warrant.
    """
    data = request.json or {}
    plate = data.get('license_plate', '').strip()
    reason = data.get('reason', 'Exceeded 15-year commercial service life without valid fitness certificate.')
    
    if not plate:
        return jsonify({'error': 'License plate is required'}), 400

    db = SessionLocal()
    try:
        result = fc_service.issue_destruction_order(plate, reason=reason, db_session=db)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    finally:
        db.close()


@fc_bp.route('/confirm-scrapping', methods=['POST'])
def confirm_scrapping():
    """
    Confirms physical vehicle destruction at Registered Vehicle Scrapping Facility (RVSF).
    """
    data = request.json or {}
    plate = data.get('license_plate', '').strip()
    facility = data.get('scrapping_facility', 'RVSF National Eco-Scrap Center #04')
    officer_badge = data.get('officer_badge', 'SEC-CMD-01')

    if not plate:
        return jsonify({'error': 'License plate is required'}), 400

    db = SessionLocal()
    try:
        result = fc_service.confirm_scrapping_destruction(
            plate, scrapping_facility=facility, officer_badge=officer_badge, db_session=db
        )
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    finally:
        db.close()


@fc_bp.route('/pay-fine', methods=['POST'])
def pay_fc_fine():
    """
    Records payment of penalty challan for expired FC violation.
    """
    data = request.json or {}
    plate = data.get('license_plate', '').strip()
    amount = data.get('amount', None)
    payment_ref = data.get('payment_ref', None)

    if not plate:
        return jsonify({'error': 'License plate is required'}), 400

    db = SessionLocal()
    try:
        result = fc_service.pay_fc_fine(plate, amount=amount, payment_ref=payment_ref, db_session=db)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    finally:
        db.close()


@fc_bp.route('/police-notice/<string:license_plate>', methods=['GET'])
def get_police_notice(license_plate):
    """
    Generates a structured official Police / RTO Notice for display or printing.
    """
    db = SessionLocal()
    try:
        clean_plate = license_plate.replace(" ", "").upper()
        record = db.query(VehicleFCRegistry).filter(
            VehicleFCRegistry.license_plate == clean_plate
        ).first()

        if not record:
            res = fc_service.verify_fc_status(clean_plate, db_session=db)
            record = db.query(VehicleFCRegistry).filter(VehicleFCRegistry.license_plate == clean_plate).first()

        d = record.to_dict()
        is_scrap = (d['police_action_required'] == 'DESTROY_VEHICLE_SCRAP' or d['vehicle_age_years'] >= 15)

        notice = {
            'notice_number': d['police_notice_number'] or f"POL-NOTICE-2026-{abs(hash(clean_plate)) % 90000 + 10000}",
            'issuing_authority': 'Government of India - Ministry of Road Transport & Highways (MoRTH) / Highway Traffic Police Command',
            'statute': 'Section 56 & 192 of Motor Vehicles Act (1988/2019) & National Vehicle Scrappage Policy (RVSF Regulations)',
            'date_issued': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
            'license_plate': clean_plate,
            'owner_name': d['owner_name'],
            'vehicle_type': d['vehicle_type'],
            'vehicle_age': f"{d['vehicle_age_years']} Years",
            'fc_status': d['fc_status'],
            'fc_expiry_date': d['fc_expiry_date'],
            'police_action_required': d['police_action_required'],
            'fine_amount': d['fine_amount'],
            'action_summary': (
                "MANDATORY IMPOUND & SCRAPPING ORDER: This commercial vehicle has exceeded 15 years of legal service lifespan and has expired fitness certification. Vehicle must be impounded immediately and surrendered to an authorized Registered Vehicle Scrapping Facility (RVSF)."
                if is_scrap else
                "MANDATORY FC RENEWAL & INSPECTION ORDER: This vehicle is operating on public highways with an expired Fitness Certificate. The registered owner must pay the statutory fine of ₹5,000 and undergo automated fitness inspection within 15 days."
            ),
            'order_type': 'DESTRUCTION_ORDER' if is_scrap else 'RENEWAL_ORDER'
        }
        return jsonify(notice)
    finally:
        db.close()
