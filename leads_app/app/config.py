import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', '/mnt/c/OneDrive/Hermes/trading_journal.db')
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '/leads')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() in ('1', 'true', 'yes')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    APPWRITE_URL = os.environ.get('APPWRITE_URL', 'http://localhost:8080')
    APPWRITE_PROJECT_ID = os.environ.get('APPWRITE_PROJECT_ID', '')
    APPWRITE_API_KEY = os.environ.get('APPWRITE_API_KEY', '')  # for Admin calls
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 1 week
