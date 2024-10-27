import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///' + os.path.join(basedir, 'test_db.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig(Config): 
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI') or 'sqlite:///' + os.path.join(basedir, 'test_db.sqlite')
    DEBUG = True
    CLOUD_STORAGE_ENABLED = False  # Desabilita o Cloud Storage nos testes
    CLOUD_STORAGE_BUCKET = 'your-bucket-name-for-tests'  # Define o bucket para testes