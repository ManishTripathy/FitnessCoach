import firebase_admin
from firebase_admin import credentials, firestore, storage
from backend.core.config import settings
import os

_db = None
_bucket = None

def initialize_firebase():
    global _db, _bucket
    try:
        if not firebase_admin._apps:
            print(f"Initializing Firebase with credentials from: {settings.FIREBASE_CREDENTIALS_PATH}")
            if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                })
                print("Firebase initialized successfully.")
            else:
                print(f"Warning: Firebase credentials not found at {settings.FIREBASE_CREDENTIALS_PATH}")
                # Try relative path as fallback
                fallback_path = "firebase-credentials.json"
                if os.path.exists(fallback_path):
                     print(f"Found credentials at fallback path: {fallback_path}")
                     cred = credentials.Certificate(fallback_path)
                     firebase_admin.initialize_app(cred, {
                        'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                     })
                else:
                    return False
        
        _db = firestore.client()
        try:
             _bucket = storage.bucket()
        except Exception as e:
             print(f"Warning: Could not get storage bucket: {e}")
             _bucket = None
             
        return True
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_db():
    global _db
    if _db is None:
        initialize_firebase()
    return _db

def get_bucket():
    global _bucket
    if _bucket is None:
        initialize_firebase()
    return _bucket

def download_file_as_bytes(storage_path: str) -> bytes:
    """Download a file from Firebase Storage as bytes."""
    bucket = get_bucket()
    if not bucket:
        raise Exception("Storage bucket not initialized")
    blob = bucket.blob(storage_path)
    return blob.download_as_bytes()

def save_anonymous_session(session_id: str, data: dict):
    """Save anonymous session data to Firestore."""
    db = get_db()
    if not db:
        raise Exception("Firestore not initialized")
    
    # Merge with existing data if any
    doc_ref = db.collection('anonymous_sessions').document(session_id)
    doc_ref.set(data, merge=True)

def get_anonymous_session(session_id: str) -> dict:
    """Get anonymous session data from Firestore."""
    db = get_db()
    if not db:
        raise Exception("Firestore not initialized")
    
    doc_ref = db.collection('anonymous_sessions').document(session_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None

def delete_anonymous_session(session_id: str):
    """Delete anonymous session data from Firestore."""
    db = get_db()
    if not db:
        raise Exception("Firestore not initialized")
    
    db.collection('anonymous_sessions').document(session_id).delete()

def check_firebase_connection():
    status = {
        "initialized": False,
        "firestore": "unknown",
        "storage": "unknown",
        "error": None
    }
    
    try:
        if not firebase_admin._apps:
             if not initialize_firebase():
                 status["error"] = "Firebase not initialized (credentials missing or invalid)"
                 return status

        status["initialized"] = True
        
        # Check Firestore
        try:
            db = get_db()
            if db:
                # Try to list collections (empty list is fine, just checking connectivity)
                # Note: collections() returns a generator/iterator
                cols = db.collections()
                # Just try to get the first one to verify access
                next(cols, None)
                status["firestore"] = "connected"
            else:
                status["firestore"] = "not_initialized"
        except Exception as e:
            status["firestore"] = f"error: {str(e)}"

        # Check Storage
        try:
            bucket = get_bucket()
            if bucket:
                # Check if bucket exists/is accessible
                if bucket.exists():
                    status["storage"] = f"connected (bucket: {bucket.name})"
                else:
                    status["storage"] = f"error: bucket {bucket.name} not found"
            else:
                 status["storage"] = "not_initialized"
        except Exception as e:
            status["storage"] = f"error: {str(e)}"

    except Exception as e:
        status["error"] = str(e)
        
    return status
