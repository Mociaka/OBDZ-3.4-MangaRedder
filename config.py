import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://manga_user:manga_password@localhost:5432/manga_db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
