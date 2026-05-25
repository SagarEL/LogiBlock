from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from routes.auth import role_required
from models import db, User, Warehouse, Route, RouteWarehouse, Shipment, Alert, BlockModel
import uuid
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('Admin')
def dashboard():
    total_shipments = Shipment.query.count()
    active_shipments = Shipment.query.filter(Shipment.status.in_(['Created', 'In Transit'])).count()
    suspicious_shipments = Shipment.query.filter_by(status='Suspicious').count()
    alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(5).all()
    
    from app import blockchain
    is_valid, _ = blockchain.validate_chain()
    status = "Secure" if is_valid else "Compromised"
    
    return render_template('admin/dashboard.html', 
                           total=total_shipments, 
                           active=active_shipments,
                           suspicious=suspicious_shipments,
                           status=status,
                           alerts=alerts)

@admin_bp.route('/warehouses', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def warehouses():
    if request.method == 'POST':
        wid = request.form.get('warehouse_id')
        name = request.form.get('warehouse_name')
        loc = request.form.get('location')
        code = request.form.get('warehouse_code')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        
        wh = Warehouse(warehouse_id=wid, warehouse_name=name, location=loc, warehouse_code=code, lat=float(lat) if lat else None, lng=float(lng) if lng else None)
        db.session.add(wh)
        db.session.commit()
        flash('Warehouse added', 'success')
        return redirect(url_for('admin.warehouses'))
        
    whs = Warehouse.query.all()
    return render_template('admin/warehouses.html', warehouses=whs)

@admin_bp.route('/routes', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def routes():
    if request.method == 'POST':
        source = request.form.get('source')
        dest = request.form.get('destination')
        wh_ids = request.form.getlist('warehouses') 
        
        rid = "RT-" + str(uuid.uuid4())[:8].upper()
        from app import blockchain
        r_hash = blockchain.generate_route_hash(wh_ids)
        
        new_route = Route(route_id=rid, source=source, destination=dest, route_hash=r_hash)
        db.session.add(new_route)
        db.session.flush() 
        
        for i, wh_id in enumerate(wh_ids):
            wh = Warehouse.query.filter_by(warehouse_id=wh_id).first()
            if wh:
                rw = RouteWarehouse(route_id=new_route.id, warehouse_id=wh.id, sequence_order=i+1)
                db.session.add(rw)
                
        db.session.commit()
        flash('Route created successfully', 'success')
        return redirect(url_for('admin.routes'))
        
    all_routes = Route.query.all()
    whs = Warehouse.query.all()
    return render_template('admin/routes.html', routes=all_routes, warehouses=whs)

@admin_bp.route('/shipments', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def shipments():
    if request.method == 'POST':
        route_id = request.form.get('route_id') 
        sender = request.form.get('sender')
        receiver = request.form.get('receiver')
        agent_id = request.form.get('agent_id')
        
        sid = "SHP-" + str(uuid.uuid4())[:8].upper()
        
        import random
        import hashlib
        pin = str(random.randint(100000, 999999))
        pin_hash = hashlib.sha256(pin.encode('utf-8')).hexdigest()
        
        shipment = Shipment(
            shipment_id=sid,
            route_id=route_id,
            sender=sender,
            receiver=receiver,
            status='Created',
            current_location='Source',
            delivery_agent_id=agent_id,
            delivery_pin=pin,
            delivery_pin_hash=pin_hash
        )
        db.session.add(shipment)
        db.session.commit()
        
        import qrcode, os
        from config import Config
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(request.host_url[:-1] + url_for('warehouse.verify', shipment_id=sid))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(os.path.join(Config.QR_FOLDER, f"{sid}.png"))

        from app import blockchain
        blockchain.add_block(sid, "SHIPMENT_CREATED", {
            "action": "CREATED",
            "sender": sender,
            "receiver": receiver,
            "route_id": Route.query.get(route_id).route_id,
            "delivery_pin_hash": pin_hash
        })
        
        flash(f'Shipment created. Secret PIN for client: {pin}', 'success')
        return redirect(url_for('admin.shipments'))
        
    shps = Shipment.query.all()
    rts = Route.query.all()
    agents = User.query.filter_by(role='Delivery').all()
    return render_template('admin/shipments.html', shipments=shps, routes=rts, agents=agents)

@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def users():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        r = request.form.get('role')
        user = User(username=u, password_hash=generate_password_hash(p), role=r)
        db.session.add(user)
        db.session.commit()
        flash('User added', 'success')
        return redirect(url_for('admin.users'))
        
    usrs = User.query.all()
    return render_template('admin/users.html', users=usrs)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_user(user_id):
    from flask_login import current_user
    if current_user.id == user_id:
        flash('You cannot delete your own admin account.', 'error')
        return redirect(url_for('admin.users'))
        
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted successfully.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/blockchain')
@login_required
@role_required('Admin')
def view_blockchain():
    from app import blockchain
    chain = blockchain.get_chain()
    
    grouped_chain = {}
    for b in chain:
        sid = b.shipment_id if b.shipment_id else "System Blocks"
        if sid not in grouped_chain:
            grouped_chain[sid] = []
        grouped_chain[sid].append(b)
        
    return render_template('common/blockchain.html', grouped_chain=grouped_chain)

@admin_bp.route('/optimize_route', methods=['GET'])
@login_required
@role_required('Admin')
def optimize_route():
    source_code = request.args.get('source')
    dest_code = request.args.get('destination')
    
    if not source_code or not dest_code:
        return jsonify({'error': 'Source and destination are required'}), 400
        
    from routing import build_warehouse_graph, dijkstra
    import math
    
    graph = build_warehouse_graph()
    cost, path = dijkstra(graph, source_code, dest_code)
    
    if math.isinf(cost) or not path:
        return jsonify({'error': 'No route found between selected warehouses'}), 404
        
    warehouses_path = []
    for code in path:
        wh = Warehouse.query.filter_by(warehouse_code=code).first()
        if wh:
            warehouses_path.append({
                'warehouse_id': wh.warehouse_id,
                'warehouse_name': wh.warehouse_name,
                'warehouse_code': wh.warehouse_code,
                'lat': wh.lat,
                'lng': wh.lng
            })
            
    return jsonify({
        'cost_km': round(cost, 2),
        'path': warehouses_path
    })

@admin_bp.route('/validate')
@login_required
@role_required('Admin')
def validate():
    from app import blockchain
    is_valid, idx = blockchain.validate_chain()
    chain = blockchain.get_chain()
    
    broken_block_info = None
    if not is_valid and idx != -1:
        broken_block = BlockModel.query.filter_by(block_index=idx).first()
        if broken_block:
            recalculated_hash = blockchain.calculate_hash(
                broken_block.block_index,
                broken_block.previous_hash,
                broken_block.timestamp,
                broken_block.data,
                broken_block.block_type,
                broken_block.warehouse_id,
                broken_block.route_hash
            )
            broken_block_info = {
                'block_index': broken_block.block_index,
                'block_type': broken_block.block_type,
                'stored_hash': broken_block.current_hash,
                'recalculated_hash': recalculated_hash,
                'stored_data': broken_block.data,
                'previous_hash': broken_block.previous_hash,
                'authentic_hash': None,
                'authentic_data': None
            }
            
    return render_template('admin/validate.html', 
                           is_valid=is_valid, 
                           invalid_index=idx, 
                           chain=chain, 
                           broken_block_info=broken_block_info)

@admin_bp.route('/simulate_tamper', methods=['POST'])
@login_required
@role_required('Admin')
def simulate_tamper():
    from app import blockchain
    blockchain.simulate_tampering()
    flash('Simulated tampering successfully!', 'warning')
    return redirect(url_for('admin.validate'))

@admin_bp.route('/restore_integrity', methods=['POST'])
@login_required
@role_required('Admin')
def restore_integrity():
    flash('Self-healing is currently unavailable because the cloud sync layer was removed.', 'error')
    return redirect(url_for('admin.validate'))
