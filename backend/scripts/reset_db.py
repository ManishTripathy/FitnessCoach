import sys
import os
import argparse

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from backend.services.firebase_service import get_db

def reset_workout_library():
    print("Initializing Firebase...")
    db = get_db()
    if not db:
        print("Failed to connect to Firebase.")
        return

    collection_ref = db.collection('workout_library')
    docs = list(collection_ref.stream())
    
    if not docs:
        print("Collection 'workout_library' is already empty.")
        return

    print(f"Found {len(docs)} documents in 'workout_library'. Deleting...")
    
    batch = db.batch()
    count = 0
    total_deleted = 0
    
    for doc in docs:
        batch.delete(doc.reference)
        count += 1
        
        # Commit every 20 deletes (limit is 500, but safer to be smaller)
        if count >= 20:
            batch.commit()
            total_deleted += count
            print(f"Deleted {total_deleted} documents...")
            batch = db.batch()
            count = 0
            
    if count > 0:
        batch.commit()
        total_deleted += count
        
    print(f"Successfully deleted {total_deleted} documents from 'workout_library'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset workout_library collection")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    if args.force:
        reset_workout_library()
    else:
        # Ask for confirmation
        confirm = input("This will DELETE ALL DATA in 'workout_library' collection. Are you sure? (y/n): ")
        if confirm.lower() == 'y':
            reset_workout_library()
        else:
            print("Operation cancelled.")
