from firebase_config import get_db

def sync_shipment_to_firebase(shipment):
    """
    Syncs the shipment data from SQLite to Firebase Firestore.
    This enables real-time tracking on the frontend!
    """
    db = get_db()
    if not db:
        print("Firebase not initialized. Skipping sync.")
        return
        
    try:
        from firebase_admin import firestore
        
        # Create a dictionary of the shipment data to sync
        shipment_data = {
            'shipment_id': shipment.shipment_id,
            'sender': shipment.sender,
            'receiver': shipment.receiver,
            'status': shipment.status,
            'current_location': shipment.current_location,
            'eta': shipment.eta,
            # Handle possible null agent
            'delivery_agent': shipment.agent.username if shipment.agent else "Unassigned",
            'last_updated': firestore.SERVER_TIMESTAMP
        }
        
        # Write to the 'shipments' collection, using the shipment_id as the document ID
        doc_ref = db.collection('shipments').document(shipment.shipment_id)
        doc_ref.set(shipment_data, merge=True)
        print(f"✅ Successfully synced Shipment {shipment.shipment_id} to Firebase!")
        
    except Exception as e:
        print(f"❌ Failed to sync shipment {shipment.shipment_id} to Firebase: {e}")
