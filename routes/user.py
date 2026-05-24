from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from routes.auth import role_required
from models import db, Shipment, BlockModel

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
@role_required('user')
def dashboard():
    return render_template('user/dashboard.html')

@user_bp.route('/track', methods=['GET', 'POST'])
@login_required
@role_required('user')
def track():
    if request.method == 'POST':
        shipment_id = request.form.get('shipment_id')
        return redirect(url_for('user.tracking', shipment_id=shipment_id))
    return render_template('user/dashboard.html')

@user_bp.route('/tracking/<shipment_id>')
@login_required
@role_required('user')
def tracking(shipment_id):
    shipment = Shipment.query.filter_by(shipment_id=shipment_id).first_or_404()
    blocks = BlockModel.query.filter_by(shipment_id=shipment_id).order_by(BlockModel.block_index.asc()).all()
    
    timeline = []
    import json
    from datetime import datetime
    for b in blocks:
        try:
            details = json.loads(b.data)
        except:
            details = b.data
            
        timeline.append({
            'status': b.block_type.replace('_', ' ').title(),
            'timestamp': datetime.fromtimestamp(b.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'details': details,
            'block_type': b.block_type,
            'warehouse_id': b.warehouse_id,
            'verification_status': b.verification_status
        })
        
    # Get the route's full warehouse list and coordinates
    from models import RouteWarehouse
    route_warehouses = RouteWarehouse.query.filter_by(route_id=shipment.route_id).order_by(RouteWarehouse.sequence_order.asc()).all()
    route_path = []
    for rw in route_warehouses:
        route_path.append({
            'name': rw.warehouse.warehouse_name,
            'code': rw.warehouse.warehouse_code,
            'lat': rw.warehouse.lat,
            'lng': rw.warehouse.lng,
            'sequence': rw.sequence_order
        })
        
    # Find list of verified checkpoints (warehouse codes) from blocks
    verified_checkpoints = []
    for b in blocks:
        if b.block_type == 'WAREHOUSE_VERIFIED' and b.verification_status == 'SUCCESS' and b.warehouse_id:
            verified_checkpoints.append(b.warehouse_id)
            
    return render_template('user/tracking.html', 
                           shipment=shipment, 
                           timeline=timeline, 
                           route_path=route_path,
                           verified_checkpoints=verified_checkpoints)
