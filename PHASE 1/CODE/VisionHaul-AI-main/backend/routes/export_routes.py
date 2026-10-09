from flask import Blueprint, send_file, request, jsonify
from backend.database.db import SessionLocal
from backend.database.models import TruckLog
from backend.services.export_service import ExportService
from datetime import datetime

export_bp = Blueprint('export_bp', __name__)

@export_bp.route('/csv', methods=['GET'])
def download_csv():
    """
    Downloads historical truck surveillance logs as CSV.
    """
    db = SessionLocal()
    try:
        logs = db.query(TruckLog).order_by(TruckLog.created_at.desc()).limit(1000).all()
        logs_data = [l.to_dict() for l in logs]
        
        csv_stream = ExportService.export_csv(logs_data)
        filename = f"truck_surveillance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            csv_stream,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    finally:
        db.close()


@export_bp.route('/pdf', methods=['GET'])
def download_pdf():
    """
    Downloads historical truck surveillance logs as formatted PDF.
    """
    db = SessionLocal()
    try:
        logs = db.query(TruckLog).order_by(TruckLog.created_at.desc()).limit(100).all()
        logs_data = [l.to_dict() for l in logs]
        
        pdf_stream = ExportService.export_pdf(logs_data)
        filename = f"truck_surveillance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_stream,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    finally:
        db.close()
