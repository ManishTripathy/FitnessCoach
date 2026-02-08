
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.services.firebase_service import get_db

def check_db():
    print("Checking database...")
    db = get_db()
    if not db:
        print("Database connection failed.")
        return

    collection = db.collection('workout_library')
    docs = list(collection.stream())
    print(f"Found {len(docs)} documents in 'workout_library'.")
    
    if len(docs) > 0:
        first_doc = docs[0].to_dict()
        print(f"Sample document ID: {docs[0].id}")
        if 'embedding' in first_doc:
            print("Sample document HAS 'embedding' field.")
            print(f"Embedding type: {type(first_doc['embedding'])}")
            print(f"Embedding length: {len(first_doc['embedding'])}")
            if len(first_doc['embedding']) > 0:
                print(f"First element type: {type(first_doc['embedding'][0])}")
        else:
            print("Sample document MISSING 'embedding' field.")
            
        print("Sample title:", first_doc.get('title'))

if __name__ == "__main__":
    check_db()
