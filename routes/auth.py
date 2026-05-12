from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user, login_required
from models import User
from werkzeug.security import check_password_hash
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def redirect_based_on_role(role):
    r = role.lower()
    if r == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif r == 'warehouse':
        return redirect(url_for('warehouse.dashboard'))
    elif r == 'delivery':
        return redirect(url_for('delivery.dashboard'))
    elif r == 'user':
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role.lower() != role.lower():
                flash('Access Denied. Unauthorized for your role.', 'error')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user.role)
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect_based_on_role(user.role)
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
