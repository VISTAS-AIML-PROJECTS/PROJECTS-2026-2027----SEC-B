import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from backend.config import Config
from backend.database.models import AlertLog
from backend.database.db import SessionLocal

class AlertManager:
    """
    Alert Manager Core Module.
    Dispatches alerts across Sound, Email, and Dashboard notification channels.
    """
    def __init__(self):
        self.recent_alerts = [] # In-memory queue of recent alerts
        self.dispatched_keys = set() # Avoid alert spam for same track/event within 10 seconds

    def trigger_alert(self, alert_type, track_id, license_plate, speed, message, severity='HIGH', db_session=None):
        """
        Dispatches alert across channels and logs to database.
        """
        # Deduplication key
        dedup_key = f"{alert_type}_{license_plate}_{int(datetime.now().timestamp() // 10)}"
        if dedup_key in self.dispatched_keys:
            return None
        self.dispatched_keys.add(dedup_key)
        
        close_db = False
        if db_session is None:
            db_session = SessionLocal()
            close_db = True

        email_success = False
        try:
            # 1. Send Email Notification if enabled
            if Config.EMAIL_ALERT_ENABLED and severity in ['HIGH', 'CRITICAL']:
                email_success = self._send_email_notification(alert_type, license_plate, speed, message, severity)

            # 2. Log to Database
            alert_entry = AlertLog(
                timestamp=datetime.now(timezone.utc),
                alert_type=alert_type,
                severity=severity,
                track_id=track_id,
                license_plate=license_plate,
                speed=speed,
                message=message,
                sound_played=Config.SOUND_ALERT_ENABLED,
                email_sent=email_success,
                acknowledged=False
            )
            db_session.add(alert_entry)
            db_session.commit()
            
            alert_dict = alert_entry.to_dict()
            self.recent_alerts.insert(0, alert_dict)
            if len(self.recent_alerts) > 50:
                self.recent_alerts.pop()
                
            print(f"[ALERT MANAGER] {severity} {alert_type}: {message}")
            return alert_dict
        except Exception as e:
            print(f"[ERROR] Error dispatching alert: {e}")
            if db_session:
                db_session.rollback()
            return None
        finally:
            if close_db:
                db_session.close()

    def _send_email_notification(self, alert_type, license_plate, speed, message, severity):
        """
        Sends email via SMTP. Falls back gracefully if credentials are not configured.
        """
        recipient = Config.ALERT_EMAIL_RECIPIENT
        if not recipient:
            return False

        subject = f"[{severity} SECURITY ALERT] {alert_type} Detected - Plate: {license_plate}"
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0b0f19; color: #ffffff; padding: 20px;">
            <div style="background-color: #1e293b; border-left: 6px solid {'#ef4444' if severity=='CRITICAL' else '#f59e0b'}; padding: 20px; border-radius: 8px;">
                <h2 style="color: {'#ef4444' if severity=='CRITICAL' else '#f59e0b'}; margin-top: 0;">AUTOMATED SURVEILLANCE NOTIFICATION</h2>
                <p><strong>Alert Type:</strong> {alert_type}</p>
                <p><strong>Severity:</strong> {severity}</p>
                <p><strong>License Plate:</strong> {license_plate}</p>
                <p><strong>Speed:</strong> {speed} km/h</p>
                <p><strong>Details:</strong> {message}</p>
                <p><strong>Timestamp:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <hr style="border-color: #334155;"/>
                <p style="font-size: 12px; color: #94a3b8;">This is an automated dispatch from VisionHaul Heavy Vehicle CCTV AI Monitoring System.</p>
            </div>
        </body>
        </html>
        """
        
        # If SMTP username/password are not set, simulate successful delivery
        if not Config.SMTP_USERNAME or not Config.SMTP_PASSWORD:
            print(f"[EMAIL SIMULATED DISPATCH] Sent to {recipient}: {subject}")
            return True

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = Config.SMTP_USERNAME
            msg['To'] = recipient
            msg.attach(MIMEText(body_html, 'html'))

            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.sendmail(Config.SMTP_USERNAME, recipient, msg.as_string())
            print(f"📧 [EMAIL SENT] Successfully dispatched to {recipient}")
            return True
        except Exception as e:
            print(f"⚠️ SMTP Send Failed (continuing): {e}")
            return False

alert_manager = AlertManager()
