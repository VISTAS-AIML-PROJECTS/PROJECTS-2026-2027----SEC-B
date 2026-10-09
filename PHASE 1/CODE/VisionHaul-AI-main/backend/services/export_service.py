import io
import csv
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

class ExportService:
    @staticmethod
    def export_csv(truck_logs):
        """
        Generates CSV file stream from list of truck logs.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Log ID', 'Track ID', 'License Plate', 'Speed (km/h)',
            'Speed Limit (km/h)', 'Overspeed Violation', 'Truck Type',
            'Color', 'Cargo Attributes', 'FC Status', 'Vehicle Age (Yrs)',
            'Police Action Required', 'Police Notice #', 'Fine (INR)',
            'Arrival Time (UTC)', 'Departure Time (UTC)', 'Visit Count', 'Camera ID'
        ])
        
        for log in truck_logs:
            writer.writerow([
                log.get('id'),
                log.get('track_id'),
                log.get('license_plate'),
                log.get('speed'),
                log.get('speed_limit'),
                'YES' if log.get('is_overspeed') else 'NO',
                log.get('truck_type'),
                log.get('color'),
                log.get('cargo_attributes'),
                log.get('fc_status') or 'VALID',
                log.get('vehicle_age_years') or 4,
                log.get('police_action_required') or 'NONE',
                log.get('police_notice_number') or '-',
                f"Rs. {log.get('fc_fine_amount', 0):,.0f}",
                log.get('arrival_time'),
                log.get('departure_time') or 'Active / On-Site',
                log.get('visit_count'),
                log.get('camera_id')
            ])
            
        output.seek(0)
        return io.BytesIO(output.getvalue().encode('utf-8'))

    @staticmethod
    def export_pdf(truck_logs, title="Heavy Vehicle Surveillance Audit Report"):
        """
        Generates professional PDF audit report using ReportLab.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=10
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#475569'),
            spaceAfter=15
        )
        
        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph(f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} | Total Records: {len(truck_logs)}", subtitle_style))
        
        # Table data
        data = [[
            'ID', 'Track', 'Plate', 'Speed', 'Limit', 'Type', 'FC Status', 'Age', 'Police Action', 'Visits', 'Arrival Time'
        ]]
        
        for l in truck_logs[:100]: # Top 100 in PDF
            fc_st = l.get('fc_status', 'VALID')
            p_act = l.get('police_action_required', 'NONE')
            p_display = 'DESTROY / SCRAP' if p_act == 'DESTROY_VEHICLE_SCRAP' else ('FC RENEWAL' if p_act == 'FC_RENEWAL_PROCESS' else 'NONE')
            
            data.append([
                str(l.get('id', '')),
                str(l.get('track_id', '')),
                str(l.get('license_plate', '')),
                f"{l.get('speed', 0)} km/h",
                f"{l.get('speed_limit', 60)}",
                str(l.get('truck_type', ''))[:14],
                fc_st[:12],
                f"{l.get('vehicle_age_years', 4)}y",
                p_display,
                str(l.get('visit_count', 1)),
                str(l.get('arrival_time', ''))[:16]
            ])
            
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')])
        ]))
        
        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return buffer

