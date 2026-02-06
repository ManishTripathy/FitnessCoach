import argparse
import sys
import os
import asyncio
# Monkey patch for httpx compatibility before importing youtube-search-python
import httpx
from youtubesearchpython.core.requests import RequestCore
from youtubesearchpython.core.constants import userAgent

def patched_syncPostRequest(self) -> httpx.Response:
    return httpx.post(
        self.url,
        headers={"User-Agent": userAgent},
        json=self.data,
        timeout=self.timeout
    )

def patched_syncGetRequest(self) -> httpx.Response:
    return httpx.get(
        self.url,
        headers={"User-Agent": userAgent},
        timeout=self.timeout,
        cookies={'CONSENT': 'YES+1'}
    )

RequestCore.syncPostRequest = patched_syncPostRequest
RequestCore.syncGetRequest = patched_syncGetRequest

from youtubesearchpython import VideosSearch
import firebase_admin
from firebase_admin import credentials, firestore

# Add backend directory to path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from backend.services.ai_service import generate_text_embedding
from backend.core.config import settings

# Initialize Firebase (reuse existing logic or new)
def initialize_firebase():
    try:
        if not firebase_admin._apps:
            cred_path = os.path.join(os.path.dirname(__file__), '../firebase-credentials.json')
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("Firebase Admin Initialized with credentials file.")
            else:
                firebase_admin.initialize_app()
                print("Firebase Admin Initialized with default credentials.")
        return firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return None

def parse_duration(duration_str):
    """Converts 'MM:SS' or 'HH:MM:SS' to minutes (int)."""
    try:
        parts = list(map(int, duration_str.split(':')))
        if len(parts) == 2:
            return parts[0] + (1 if parts[1] >= 30 else 0)
        elif len(parts) == 3:
            return parts[0] * 60 + parts[1] + (1 if parts[2] >= 30 else 0)
        return 0
    except:
        return 20 # Default fallback

def infer_focus(title):
    """Simple keyword matching to infer focus."""
    title_lower = title.lower()
    focus = []
    if "leg" in title_lower or "glute" in title_lower:
        focus.extend(["Legs", "Glutes"])
    if "arm" in title_lower or "upper" in title_lower or "shoulder" in title_lower:
        focus.extend(["Upper Body", "Arms"])
    if "abs" in title_lower or "core" in title_lower:
        focus.extend(["Abs", "Core"])
    if "hiit" in title_lower or "cardio" in title_lower:
        focus.extend(["Cardio", "HIIT"])
    if "full body" in title_lower:
        focus.append("Full Body")
    
    if not focus:
        focus.append("General Fitness")
    return list(set(focus))

def fetch_videos_from_youtube(trainer_name, limit=5):
    """Fetches videos for a trainer using youtube-search-python."""
    print(f"Searching for workouts by {trainer_name}...")
    query = f"{trainer_name} workout"
    videos_search = VideosSearch(query, limit=limit)
    results = videos_search.result()
    
    workouts = []
    
    if 'result' in results:
        for video in results['result']:
            try:
                title = video.get('title')
                link = video.get('link')
                duration_str = video.get('duration')
                thumbnails = video.get('thumbnails', [])
                thumbnail_url = thumbnails[0]['url'] if thumbnails else ""
                
                # Create a unique ID from the video ID
                video_id = video.get('id')
                doc_id = f"{trainer_name.lower().replace(' ', '_')}_{video_id}"
                
                # Infer details
                duration_mins = parse_duration(duration_str)
                focus = infer_focus(title)
                
                workout = {
                    "id": doc_id,
                    "title": title,
                    "trainer": trainer_name,
                    "url": link,
                    "duration_mins": duration_mins,
                    "difficulty": "Intermediate", # Default
                    "focus": focus,
                    "description": f"Workout by {trainer_name}: {title}",
                    "thumbnail": thumbnail_url
                }
                workouts.append(workout)
            except Exception as e:
                print(f"Skipping video due to error: {e}")
                
    return workouts

def seed_data(trainers, limit):
    db = initialize_firebase()
    if not db:
        print("Database connection failed. Exiting.")
        return

    collection_ref = db.collection('workout_library')
    total_added = 0

    for trainer in trainers:
        videos = fetch_videos_from_youtube(trainer, limit)
        
        for workout in videos:
            # Generate embedding
            text_to_embed = f"{workout['title']} {workout['description']} {' '.join(workout['focus'])}"
            embedding = generate_text_embedding(text_to_embed)
            
            if not embedding:
                print(f"Failed to generate embedding for {workout['title']}. Skipping.")
                continue
                
            workout['embedding'] = embedding
            
            # Save to Firestore
            try:
                collection_ref.document(workout['id']).set(workout)
                print(f"Saved: {workout['title']}")
                total_added += 1
            except Exception as e:
                print(f"Error saving {workout['id']}: {e}")

    print(f"\nSuccessfully seeded {total_added} workouts.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed workout data from YouTube.")
    parser.add_argument("--trainers", nargs="+", default=["Caroline Girvan", "Sydney Cummings"], help="List of trainer names to search for")
    parser.add_argument("--limit", type=int, default=5, help="Number of videos to fetch per trainer")
    
    args = parser.parse_args()
    
    seed_data(args.trainers, args.limit)
