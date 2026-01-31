import firebase_admin
from firebase_admin import credentials, firestore
import os

def check_db():
    try:
        cred_path = os.path.join(os.path.dirname(__file__), 'backend/firebase-credentials.json')
        if not os.path.exists(cred_path):
            print(f"Credentials not found at {cred_path}")
            return
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        workouts = db.collection('workout_library').stream()
        print("--- Workouts in DB ---")
        for w in workouts:
            data = w.to_dict()
            print(f"ID: {w.id}")
            print(f"Title: {data.get('title')}")
            print(f"URL: {data.get('url')}")
            print("-" * 20)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
