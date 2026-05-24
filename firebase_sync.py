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

def sync_block_to_firebase(block):
    """
    Syncs a blockchain block to Firebase Firestore.
    This creates an offsite immutable audit trail for self-healing.
    """
    db = get_db()
    if not db:
        print("Firebase not initialized. Skipping block sync.")
        return
        
    try:
        from firebase_admin import firestore
        
        block_data = {
            'block_index': block.block_index,
            'shipment_id': block.shipment_id,
            'block_type': block.block_type,
            'warehouse_id': block.warehouse_id,
            'data': block.data,
            'previous_hash': block.previous_hash,
            'current_hash': block.current_hash,
            'route_hash': block.route_hash,
            'verification_status': block.verification_status,
            'digital_proof_hash': block.digital_proof_hash,
            'timestamp': block.timestamp,
            'synced_at': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref = db.collection('blocks').document(str(block.block_index))
        doc_ref.set(block_data, merge=True)
        print(f"✅ Successfully synced Block #{block.block_index} to Firebase!")
        
    except Exception as e:
        print(f"❌ Failed to sync block #{block.block_index} to Firebase: {e}")
