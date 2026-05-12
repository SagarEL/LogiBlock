import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'super-secret-key-logiblock-v2'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database', 'logistics_v2.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    QR_FOLDER = os.path.join(BASE_DIR, 'static', 'qr')
    PROOFS_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'proofs')
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.QR_FOLDER, exist_ok=True)
        os.makedirs(Config.PROOFS_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)
