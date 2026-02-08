
import os
import sys
from google.cloud.firestore_v1.vector import Vector

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.services.firebase_service import get_db

def migrate_embeddings():
    print("Starting embedding migration to Vector type...")
    db = get_db()
    if not db:
        print("Database connection failed.")
        return

    collection = db.collection('workout_library')
    docs = list(collection.stream())
    print(f"Found {len(docs)} documents to check.")
    
    updated_count = 0
    
    for doc in docs:
        data = doc.to_dict()
        if 'embedding' in data:
            embedding = data['embedding']
            # Check if it's a list (and not already a Vector which might look like something else)
            if isinstance(embedding, list):
                print(f"Updating document {doc.id}...")
                try:
                    # Update strictly the embedding field with Vector wrapper
                    doc.reference.update({'embedding': Vector(embedding)})
                    updated_count += 1
                except Exception as e:
                    print(f"Failed to update {doc.id}: {e}")
            else:
                # It might be already a Vector or something else
                pass
                # print(f"Document {doc.id} embedding is type {type(embedding)}, skipping.")
        else:
            print(f"Document {doc.id} has no embedding.")

    print(f"Migration complete. Updated {updated_count} documents.")

if __name__ == "__main__":
    migrate_embeddings()
