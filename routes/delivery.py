from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from routes.auth import role_required
from models import db, Shipment, RouteWarehouse

delivery_bp = Blueprint('delivery', __name__)

@delivery_bp.route('/dashboard')
@login_required
@role_required('delivery')
def dashboard():
    shipments = Shipment.query.filter_by(delivery_agent_id=current_user.id).all()
    
    shipments_data = []
    for s in shipments:
        # Get the route's full warehouse list and coordinates
        from models import RouteWarehouse
        route_warehouses = RouteWarehouse.query.filter_by(route_id=s.route_id).order_by(RouteWarehouse.sequence_order.asc()).all()
        path = []
        for rw in route_warehouses:
            path.append({
                'name': rw.warehouse.warehouse_name,
                'code': rw.warehouse.warehouse_code,
                'lat': rw.warehouse.lat,
                'lng': rw.warehouse.lng,
                'sequence': rw.sequence_order
            })
            
        shipments_data.append({
            'shipment_id': s.shipment_id,
            'status': s.status,
            'current_location': s.current_location,
            'next_sequence': s.next_warehouse_sequence,
            'path': path
        })
            
    return render_template('delivery/dashboard.html', shipments=shipments, shipments_data=shipments_data)

@delivery_bp.route('/finalize_delivery/<shipment_id>', methods=['POST'])
@login_required
@role_required('delivery')
def finalize_delivery(shipment_id):
    shipment = Shipment.query.filter_by(shipment_id=shipment_id, delivery_agent_id=current_user.id).first()
    if not shipment:
        flash('Shipment not found or unauthorized', 'error')
        return redirect(url_for('delivery.dashboard'))
        
    pin = request.form.get('pin')
    if not pin:
        flash('Secret PIN is required', 'error')
        return redirect(url_for('delivery.dashboard'))
        
    import hashlib
    pin_hash = hashlib.sha256(pin.encode('utf-8')).hexdigest()
    
    if pin_hash == shipment.delivery_pin_hash:
        shipment.status = 'Delivered'
        shipment.current_location = 'Destination Reached'
        db.session.commit()
        
        from app import blockchain
        blockchain.add_block(shipment.shipment_id, "DELIVERY_COMPLETED", {
            "action": "HASHLOCK_VERIFIED",
            "message": "Delivery successfully cryptographically verified via Secret PIN."
        }, digital_proof_hash=pin_hash)
        
        flash('Hashlock verified! Delivery successfully finalized.', 'success')
    else:
        from app import blockchain
        blockchain.add_block(shipment.shipment_id, "DELIVERY_FAILED_ATTEMPT", {
            "action": "HASHLOCK_FAILED",
            "message": "Invalid PIN entered by delivery agent."
        })
        flash('Invalid Secret PIN! Failed to finalize delivery.', 'error')
        
    return redirect(url_for('delivery.dashboard'))
