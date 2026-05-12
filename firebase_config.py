import firebase_admin
from firebase_admin import credentials, firestore
import os

def init_firebase():
    """Initializes the Firebase Admin SDK. Call this from app.py."""
    # Check if we already initialized to avoid errors on hot reloads
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), 'firebase_credentials.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
        else:
            print("Warning: firebase_credentials.json not found. Firebase is NOT initialized.")

def get_db():
    """Returns the Firestore database instance."""
    if firebase_admin._apps:
        return firestore.client()
    return None
