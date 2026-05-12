from firebase_config import init_firebase, get_db

print("Initializing Firebase...")
init_firebase()
db = get_db()
if db:
    print("Firebase DB connected successfully!")
    # Test a write
    doc_ref = db.collection('test_connection').document('ping')
    doc_ref.set({
        'status': 'connected',
        'app': 'LogiBlock'
    })
    print("Successfully wrote a test document to Firestore!")
else:
    print("Failed to get DB instance.")
