from app import create_app
from models import db, Shipment, BlockModel
from firebase_sync import sync_shipment_to_firebase, sync_block_to_firebase

app = create_app()
with app.app_context():
    shipments = Shipment.query.all()
    print(f"Found {len(shipments)} shipments. Syncing to Firebase...")
    for s in shipments:
        sync_shipment_to_firebase(s)
        
    blocks = BlockModel.query.all()
    print(f"Found {len(blocks)} blocks. Syncing to Firebase...")
    for b in blocks:
        sync_block_to_firebase(b)
        
    print("All done!")
