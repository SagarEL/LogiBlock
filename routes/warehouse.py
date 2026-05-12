from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from routes.auth import role_required
from models import db, Shipment, Warehouse, RouteWarehouse, Alert
from firebase_sync import sync_shipment_to_firebase

warehouse_bp = Blueprint('warehouse', __name__)

@warehouse_bp.route('/dashboard')
@login_required
@role_required('Warehouse')
def dashboard():
    shipments = Shipment.query.filter(Shipment.status.in_(['Created', 'In Transit'])).all()
    return render_template('warehouse/dashboard.html', shipments=shipments)

@warehouse_bp.route('/verify/<shipment_id>', methods=['GET', 'POST'])
@login_required
@role_required('Warehouse')
def verify(shipment_id):
    shipment = Shipment.query.filter_by(shipment_id=shipment_id).first_or_404()
    
    if request.method == 'POST':
        wh_id = request.form.get('warehouse_id')
        wh = Warehouse.query.filter_by(warehouse_id=wh_id).first()
        
        if not wh:
            flash('Invalid Warehouse ID', 'error')
            return redirect(url_for('warehouse.verify', shipment_id=shipment_id))
            
        expected_rw = RouteWarehouse.query.filter_by(route_id=shipment.route_id, sequence_order=shipment.next_warehouse_sequence).first()
        
        from app import blockchain
        
        if expected_rw and expected_rw.warehouse_id == wh.id:
            shipment.status = 'In Transit'
            shipment.current_location = wh.warehouse_name
            shipment.next_warehouse_sequence += 1
            db.session.commit()
            sync_shipment_to_firebase(shipment)
            
            blockchain.add_block(shipment_id, "WAREHOUSE_VERIFIED", {
                "message": "Parcel verified at warehouse",
                "warehouse": wh.warehouse_name
            }, warehouse_id=wh.warehouse_id, verification_status="SUCCESS")
            
            flash('Warehouse Verified Successfully', 'success')
            
            next_rw = RouteWarehouse.query.filter_by(route_id=shipment.route_id, sequence_order=shipment.next_warehouse_sequence).first()
            if not next_rw:
                shipment.status = 'Delivered'
                db.session.commit()
                sync_shipment_to_firebase(shipment)
                blockchain.add_block(shipment_id, "DELIVERY_COMPLETED", {
                    "message": "Shipment arrived at final destination"
                })
        else:
            shipment.status = 'Suspicious'
            db.session.commit()
            sync_shipment_to_firebase(shipment)
            
            alert_id = "ALT-" + str(shipment.id) + str(wh.id)
            alert = Alert(alert_id=alert_id, shipment_id=shipment_id, alert_type="ROUTE_VIOLATION", description=f"Expected WH sequence {shipment.next_warehouse_sequence}, got {wh_id}")
            db.session.add(alert)
            db.session.commit()
            
            blockchain.add_block(shipment_id, "ROUTE_ALERT", {
                "message": "Unauthorized Warehouse Routing",
                "actual_warehouse": wh_id
            }, warehouse_id=wh_id, verification_status="FAILED")
            
            flash('ROUTE VIOLATION! Alert sent to Admin.', 'error')
            
        return redirect(url_for('warehouse.dashboard'))
        
    return render_template('warehouse/verify.html', shipment=shipment)
