from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from routes.auth import role_required
from models import db, Shipment, BlockModel

client_bp = Blueprint('client', __name__)

@client_bp.route('/dashboard')
@login_required
@role_required('Client')
def dashboard():
    return render_template('client/dashboard.html')

@client_bp.route('/track', methods=['GET', 'POST'])
@login_required
@role_required('Client')
def track():
    if request.method == 'POST':
        shipment_id = request.form.get('shipment_id')
        return redirect(url_for('client.tracking', shipment_id=shipment_id))
    return render_template('client/dashboard.html')

@client_bp.route('/tracking/<shipment_id>')
@login_required
@role_required('Client')
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
            'details': details
        })
        
    return render_template('client/tracking.html', shipment=shipment, timeline=timeline)
