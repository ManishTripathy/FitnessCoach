import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys
from dotenv import load_dotenv

# Add backend directory to path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from backend.services.ai_service import generate_text_embedding

# --- Configuration ---
# Hardcoded curated list of Caroline Girvan workouts
# Representing different categories for a balanced week
WORKOUTS = [
    {
        "id": "cg_lean_1",
        "title": "20 MIN FULL BODY WORKOUT // No Equipment | Caroline Girvan",
        "trainer": "Caroline Girvan",
        "url": "https://www.youtube.com/watch?v=1vRto-2MMZo",
        "duration_mins": 20,
        "difficulty": "Beginner/Intermediate",
        "focus": ["Full Body", "No Equipment", "Endurance"],
        "description": "A full body workout using just your bodyweight. Great for getting lean and toning up without gym equipment."
    },
    {
        "id": "cg_legs_1",
        "title": "30 MIN DUMBBELL LEG WORKOUT | Caroline Girvan",
        "trainer": "Caroline Girvan",
        "url": "https://www.youtube.com/watch?v=4Tz1LqGkQ9E",
        "duration_mins": 30,
        "difficulty": "Intermediate",
        "focus": ["Legs", "Glutes", "Strength", "Dumbbells"],
        "description": "Focused leg day using dumbbells. Targets quads, hamstrings and glutes for building definition and strength."
    },
    {
        "id": "cg_upper_1",
        "title": "15 MIN UPPER BODY WORKOUT - Shoulders & Arms | Caroline Girvan",
        "trainer": "Caroline Girvan",
        "url": "https://www.youtube.com/watch?v=u31qwQUeGuM",
        "duration_mins": 15,
        "difficulty": "Intermediate",
        "focus": ["Upper Body", "Arms", "Shoulders", "Dumbbells"],
        "description": "Quick but intense upper body blast focusing on sculpting shoulders and arms."
    },
    {
        "id": "cg_hiit_1",
        "title": "15 MIN HIIT CARDIO WORKOUT | No Equipment | Caroline Girvan",
        "trainer": "Caroline Girvan",
        "url": "https://www.youtube.com/watch?v=M0uO8X3_tEA",
        "duration_mins": 15,
        "difficulty": "High",
        "focus": ["Cardio", "HIIT", "Fat Loss"],
        "description": "High Intensity Interval Training to burn calories and improve cardiovascular health. No equipment needed."
    },
    {
        "id": "cg_abs_1",
        "title": "10 MIN AB WORKOUT // No Equipment | Caroline Girvan",
        "trainer": "Caroline Girvan",
        "url": "https://www.youtube.com/watch?v=HwrKuxq4fPA",
        "duration_mins": 10,
        "difficulty": "Intermediate",
        "focus": ["Abs", "Core"],
        "description": "Intense core session to strengthen and define the abdominals."
    },
    {
        "id": "cg_full_2",
        "title": "45 MIN IRON SERIES FULL BODY WORKOUT | Caroline Girvan",
        "trainer": "Caroline Girvan",
        "url": "https://www.youtube.com/watch?v=C3d2sVp4yWc",
        "duration_mins": 45,
        "difficulty": "Advanced",
        "focus": ["Full Body", "Strength", "Hypertrophy"],
        "description": "A longer, slower-paced strength session from the Iron Series. Focuses on muscle building and controlled movements."
    },
    {
        "id": "cg_stretch_1",
        "title": "20 MIN FULL BODY STRETCH & COOL DOWN | Caroline Girvan",
        "trainer": "Caroline Girvan",
        "url": "https://www.youtube.com/watch?v=2L2lnxIcNmo",
        "duration_mins": 20,
        "difficulty": "Easy",
        "focus": ["Recovery", "Flexibility", "Stretch"],
        "description": "Essential recovery routine to improve flexibility and reduce muscle soreness."
    }
]

def initialize_firebase():
    try:
        # Try finding credentials in backend folder
        cred_path = os.path.join(os.path.dirname(__file__), '../firebase-credentials.json')
        if not os.path.exists(cred_path):
             # Fallback to env or assume implicit if running on Google Cloud (not likely here)
             print(f"Credentials not found at {cred_path}")
             return None
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin Initialized.")
        return firestore.client()
    except Exception as e:
        print(f"Firebase Init Error: {e}")
        return None

def seed_data():
    db = initialize_firebase()
    if not db:
        return

    print(f"Seeding {len(WORKOUTS)} workouts into 'workout_library'...")
    
    collection = db.collection('workout_library')
    
    for workout in WORKOUTS:
        print(f"Processing: {workout['title']}")
        
        # 1. Generate Embedding
        # Combine relevant text for semantic search
        text_to_embed = f"{workout['title']} {workout['description']} {' '.join(workout['focus'])}"
        embedding = generate_text_embedding(text_to_embed)
        
        if not embedding:
            print(f"  - Warning: Failed to generate embedding for {workout['id']}")
        
        # 2. Prepare Document
        doc_data = workout.copy()
        doc_data['embedding'] = embedding
        doc_data['created_at'] = firestore.SERVER_TIMESTAMP
        
        # 3. Write to Firestore
        collection.document(workout['id']).set(doc_data)
        print(f"  - Saved to Firestore.")

    print("\nSeeding Complete!")

if __name__ == "__main__":
    seed_data()
