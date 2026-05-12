from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False) # Admin, Warehouse, Delivery, Client

class Warehouse(db.Model):
    __tablename__ = 'warehouses'
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.String(50), unique=True, nullable=False)
    warehouse_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    warehouse_code = db.Column(db.String(50), nullable=False)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)

class Route(db.Model):
    __tablename__ = 'routes'
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.String(50), unique=True, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    route_hash = db.Column(db.String(64), nullable=False)
    warehouses = db.relationship('RouteWarehouse', backref='route', cascade='all, delete-orphan', order_by='RouteWarehouse.sequence_order')

class RouteWarehouse(db.Model):
    __tablename__ = 'route_warehouses'
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    sequence_order = db.Column(db.Integer, nullable=False)
    warehouse = db.relationship('Warehouse')

class Shipment(db.Model):
    __tablename__ = 'shipments'
    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.String(50), unique=True, nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    receiver = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    current_location = db.Column(db.String(100), nullable=False)
    delivery_agent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    eta = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    next_warehouse_sequence = db.Column(db.Integer, default=1)
    
    route = db.relationship('Route')
    agent = db.relationship('User', foreign_keys=[delivery_agent_id])

class BlockModel(db.Model):
    __tablename__ = 'blockchain'
    id = db.Column(db.Integer, primary_key=True)
    block_index = db.Column(db.Integer, nullable=False)
    shipment_id = db.Column(db.String(50), nullable=True)
    block_type = db.Column(db.String(50), nullable=False)
    warehouse_id = db.Column(db.String(50), nullable=True)
    data = db.Column(db.Text, nullable=False)
    previous_hash = db.Column(db.String(64), nullable=False)
    current_hash = db.Column(db.String(64), nullable=False)
    route_hash = db.Column(db.String(64), nullable=True)
    verification_status = db.Column(db.String(50), nullable=True)
    digital_proof_hash = db.Column(db.String(64), nullable=True)
    timestamp = db.Column(db.Float, nullable=False)

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(50), unique=True, nullable=False)
    shipment_id = db.Column(db.String(50), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)
