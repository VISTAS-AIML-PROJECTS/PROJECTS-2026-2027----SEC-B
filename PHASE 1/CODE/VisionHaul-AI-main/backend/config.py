import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Database Settings: Defaults to SQLite for immediate zero-config runs, or MySQL if specified in MYSQL_URI env var
    DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, 'data', 'surveillance.db')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'MYSQL_URI',
        f'sqlite:///{DEFAULT_SQLITE_PATH}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Surveillance & Speed Settings
    DEFAULT_SPEED_LIMIT = float(os.getenv('SPEED_LIMIT_KMH', '60.0'))
    PIXELS_PER_METER = float(os.getenv('PIXELS_PER_METER', '18.5'))
    FPS = int(os.getenv('CAMERA_FPS', '25'))
    
    # Alert Configuration
    SOUND_ALERT_ENABLED = os.getenv('SOUND_ALERT_ENABLED', 'true').lower() == 'true'
    EMAIL_ALERT_ENABLED = os.getenv('EMAIL_ALERT_ENABLED', 'true').lower() == 'true'
    ALERT_EMAIL_RECIPIENT = os.getenv('ALERT_EMAIL_RECIPIENT', 'security.director@portlogistics.com')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    
    # Storage & Uploads
    SNAPSHOT_DIR = os.path.join(BASE_DIR, 'data', 'snapshots')
    UPLOAD_DIR = os.path.join(BASE_DIR, 'data', 'uploads')
    
    # Secret Key
    SECRET_KEY = os.getenv('SECRET_KEY', 'visionhaul-secret-security-key-2026')
