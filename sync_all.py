from app import create_app
from models import db, Shipment
from firebase_sync import sync_shipment_to_firebase

app = create_app()
with app.app_context():
    shipments = Shipment.query.all()
    print(f"Found {len(shipments)} shipments. Syncing to Firebase...")
    for s in shipments:
        sync_shipment_to_firebase(s)
    print("All done!")
