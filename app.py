import os
from flask import Flask, redirect, url_for
from config import Config
from models import db, User
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from blockchain import Blockchain
from firebase_config import init_firebase

blockchain = Blockchain()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    Config.init_app(app)
    db.init_app(app)
    init_firebase()
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.warehouse import warehouse_bp
    from routes.delivery import delivery_bp
    from routes.user import user_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(warehouse_bp, url_prefix='/warehouse')
    app.register_blueprint(delivery_bp, url_prefix='/delivery')
    app.register_blueprint(user_bp, url_prefix='/user')
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
        
    with app.app_context():
        db.create_all()
        # Seed users
        roles_to_seed = [
            ('admin', 'admin123', 'admin'),
            ('warehouse1', 'warehouse123', 'warehouse'),
            ('delivery1', 'delivery123', 'delivery'),
            ('user1', 'user123', 'user')
        ]
        for u, p, r in roles_to_seed:
            if not User.query.filter_by(username=u).first():
                user = User(username=u, password_hash=generate_password_hash(p), role=r)
                db.session.add(user)
        db.session.commit()
            
        blockchain.create_genesis_block()
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
