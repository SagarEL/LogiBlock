from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from routes.auth import role_required
from models import db, Shipment, RouteWarehouse

agent_bp = Blueprint('agent', __name__)

@agent_bp.route('/dashboard')
@login_required
@role_required('Delivery')
def dashboard():
    shipments = Shipment.query.filter_by(delivery_agent_id=current_user.id).all()
    
    map_data = []
    for s in shipments:
        next_rw = RouteWarehouse.query.filter_by(route_id=s.route_id, sequence_order=s.next_warehouse_sequence).first()
        if next_rw and next_rw.warehouse.lat and next_rw.warehouse.lng:
            map_data.append({
                'shipment_id': s.shipment_id,
                'lat': next_rw.warehouse.lat,
                'lng': next_rw.warehouse.lng,
                'name': next_rw.warehouse.warehouse_name
            })
            
    return render_template('agent/dashboard.html', shipments=shipments, map_data=map_data)
