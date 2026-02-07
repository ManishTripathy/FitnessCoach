import asyncio
import os
import sys
import json
import argparse
from typing import List, Dict, Any

# Monkey patch for httpx compatibility
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

from youtubesearchpython import PlaylistsSearch, VideosSearch
import firebase_admin
from firebase_admin import credentials, firestore

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from backend.services.ai_service import generate_text_embedding
from backend.core.config import settings

# Google ADK Imports
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.models import Gemini
from google.adk.sessions import InMemorySessionService
from google.genai import types

# --- Tools ---

def search_youtube_playlists(trainer_name: str) -> List[Dict[str, Any]]:
    """
    Searches YouTube for playlists by a specific trainer.
    Returns a list of playlists with title, id, and thumbnails.
    """
    print(f"Tool called: Searching playlists for {trainer_name}...")
    try:
        search = PlaylistsSearch(f"{trainer_name} workout", limit=15)
        results = search.result()
        
        playlists = []
        if 'result' in results:
            for item in results['result']:
                playlists.append({
                    "title": item.get('title'),
                    "id": item.get('id'),
                    "link": item.get('link'),
                    "thumbnail": item.get('thumbnails', [{}])[0].get('url', ''),
                    "channel": item.get('channel', {}).get('name')
                })
        return playlists
    except Exception as e:
        print(f"Error in search_youtube_playlists: {e}")
        return []

# --- ADK Agent Setup ---

async def get_curated_playlists(trainer_name: str) -> List[Dict[str, Any]]:
    """
    Uses an ADK Agent to search and filter playlists.
    """
    
    # 1. Define the tool for the model
    # Note: In ADK/GenAI, we define tools as function declarations
    tools = [search_youtube_playlists]
    
    # 2. Define the Agent
    system_instruction = """
    You are a strict Fitness Content Curator.
    Your goal is to find high-quality WORKOUT playlists for a given trainer.
    
    Rules:
    1. Use the `search_youtube_playlists` tool to find playlists.
    2. Filter the results aggressively.
    3. KEEP playlists that are clearly about: Workouts, Programs (e.g. "Iron Series", "Summer Shred"), Muscle Groups (e.g. "Legs", "Abs"), or specific training styles (HIIT, Yoga).
    4. DISCARD playlists that are about: Vlogs, "What I Eat in a Day", Q&A, Lifestyle, Reviews, or Shopping Hauls.
    5. Output the final list of APPROVED playlists as a JSON list.
    
    Output Format:
    Return ONLY a valid JSON array of objects. Each object must have:
    - "id": The playlist ID
    - "title": The playlist title
    - "reason": Why you approved it (e.g., "Structured workout program")
    """
    
    model = Gemini(model="gemini-2.0-flash", tools=tools)
    
    agent = Agent(
        name="playlist_curator",
        model=model,
        instruction=system_instruction
    )
    
    # 3. Define the Runner
    runner = Runner(
        agent=agent,
        app_name="fitness_coach_app",
        session_service=InMemorySessionService()
    )
    
    # 4. Execute
    user_prompt = f"Find and curate workout playlists for {trainer_name}."
    
    print(f"Agent ({agent.name}) starting curation for: {trainer_name}")

    # Explicitly create the session
    session_id = f"curation_{trainer_name.replace(' ', '_')}"
    await runner.session_service.create_session(
        app_name="fitness_coach_app",
        user_id="seed_script",
        session_id=session_id
    )
    
    final_text = ""
    async for event in runner.run_async(
        user_id="seed_script", 
        session_id=session_id, 
        new_message=types.Content(role="user", parts=[types.Part(text=user_prompt)])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_text += part.text
    
    # 5. Parse Result
    try:
        # Clean markdown code blocks if present
        cleaned_text = final_text.replace("```json", "").replace("```", "").strip()
        playlists = json.loads(cleaned_text)
        print(f"Agent selected {len(playlists)} valid playlists.")
        return playlists
    except Exception as e:
        print(f"Failed to parse agent response: {e}")
        print(f"Raw response: {final_text}")
        return []

# --- Data Seeding Logic ---

def initialize_firebase():
    try:
        if not firebase_admin._apps:
            cred_path = os.path.join(os.path.dirname(__file__), '../firebase-credentials.json')
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()
        return firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return None

def parse_duration(duration_str):
    try:
        parts = list(map(int, duration_str.split(':')))
        if len(parts) == 2:
            return parts[0] + (1 if parts[1] >= 30 else 0)
        elif len(parts) == 3:
            return parts[0] * 60 + parts[1] + (1 if parts[2] >= 30 else 0)
        return 0
    except:
        return 20

def infer_focus(title):
    title_lower = title.lower()
    focus = []
    if "leg" in title_lower or "glute" in title_lower: focus.extend(["Legs", "Glutes"])
    if "arm" in title_lower or "upper" in title_lower or "shoulder" in title_lower: focus.extend(["Upper Body", "Arms"])
    if "abs" in title_lower or "core" in title_lower: focus.extend(["Abs", "Core"])
    if "hiit" in title_lower or "cardio" in title_lower: focus.extend(["Cardio", "HIIT"])
    if "full body" in title_lower: focus.append("Full Body")
    if not focus: focus.append("General Fitness")
    return list(set(focus))

async def process_playlist(db, playlist_info, trainer_name, limit_per_playlist=5):
    """
    Fetches videos using search query combined with playlist title (Workaround for broken Playlist class).
    """
    playlist_id = playlist_info['id']
    playlist_title = playlist_info['title']
    print(f"  -> Processing Playlist: {playlist_title}")
    
    try:
        # Search for videos matching "Trainer Playlist Title workout"
        query = f"{trainer_name} {playlist_title} workout"
        search = VideosSearch(query, limit=limit_per_playlist)
        results = search.result()
        
        videos = []
        if 'result' in results:
            videos = results['result']
             
        collection_ref = db.collection('workout_library')
        count = 0
        
        for video in videos:
            try:
                title = video.get('title')
                video_id = video.get('id')
                thumbnails = video.get('thumbnails', [])
                thumbnail_url = thumbnails[0]['url'] if thumbnails else ""
                
                doc_id = f"{video_id}"
                
                duration_str = video.get('duration', '20:00')
                duration_mins = parse_duration(duration_str)
                focus = infer_focus(title)
                
                # Add playlist tag
                focus.append(f"Program: {playlist_title}")
                
                workout = {
                    "id": doc_id,
                    "title": title,
                    "trainer": trainer_name,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "duration_mins": duration_mins,
                    "difficulty": "Intermediate",
                    "focus": focus,
                    "description": f"From program: {playlist_title}. {title}",
                    "thumbnail": thumbnail_url,
                    "playlist_id": playlist_id
                }
                
                # Generate Embedding
                text_to_embed = f"{workout['title']} {workout['description']} {' '.join(workout['focus'])}"
                embedding = generate_text_embedding(text_to_embed)
                if embedding:
                    workout['embedding'] = embedding
                    collection_ref.document(doc_id).set(workout)
                    print(f"     + Saved: {title[:30]}...")
                    count += 1
                
            except Exception as e:
                print(f"     ! Error saving video: {e}")
                
        return count
        
    except Exception as e:
        print(f"  ! Error processing playlist {playlist_title}: {e}")
        return 0

async def main():
    parser = argparse.ArgumentParser(description="Seed workout data using ADK Agent curation.")
    parser.add_argument("--trainers", nargs="+", default=["Caroline Girvan"], help="Trainers to search")
    parser.add_argument("--videos_per_playlist", type=int, default=3, help="Max videos to seed per playlist")
    args = parser.parse_args()
    
    db = initialize_firebase()
    if not db: return

    total_saved = 0
    
    for trainer in args.trainers:
        print(f"\n--- Starting Curation for {trainer} ---")
        curated_playlists = await get_curated_playlists(trainer)
        
        for pl in curated_playlists:
            saved_count = await process_playlist(db, pl, trainer, args.videos_per_playlist)
            total_saved += saved_count
            
    print(f"\nTotal workouts seeded: {total_saved}")

if __name__ == "__main__":
    asyncio.run(main())
