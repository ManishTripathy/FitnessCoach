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
            if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                })
                print("Firebase initialized successfully.")
            else:
                print(f"Warning: Firebase credentials not found at {settings.FIREBASE_CREDENTIALS_PATH}")
                return False
        
        _db = firestore.client()
        _bucket = storage.bucket()
        return True
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
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
                list(db.collections(limit=1)) 
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
