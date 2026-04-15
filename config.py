import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-fallback-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///truck_rental.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@isuzu-forward.ru'
    COMPANY_NAME = os.environ.get('COMPANY_NAME') or 'Isuzu Forward Аренда'
    COMPANY_PHONE = os.environ.get('COMPANY_PHONE') or '+7 (800) 555-35-35'
    COMPANY_ADDRESS = os.environ.get('COMPANY_ADDRESS') or 'г. Москва, ул. Промышленная, д. 15'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'img', 'uploads')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
