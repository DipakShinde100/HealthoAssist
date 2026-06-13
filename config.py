import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'healthoassist-secret-key-2025')
    
    # MySQL Configuration (commented out as fallback)
    # MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    # MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    # MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    # MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'Dipak754800')
    # MYSQL_DB = os.environ.get('MYSQL_DB', 'healthoassist')
    
    # We will use SQLite for simplicity and out-of-the-box local development compatibility
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'healthoassist.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session config
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Model path
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'svc.pkl')
    
    # Data directory
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    
    # Confidence threshold for clinician referral
    CONFIDENCE_THRESHOLD = 0.40

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False