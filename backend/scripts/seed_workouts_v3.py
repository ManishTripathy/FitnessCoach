import asyncio
import os
import sys
import json
import argparse
import re
from typing import List, Dict, Any

# Google API Client
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import firebase_admin
from firebase_admin import credentials, firestore

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from backend.services.ai_service import generate_text_embedding
from backend.services.ai.core import get_runner, run_agent, extract_text_from_content
from backend.core.config import settings

# Google ADK Imports
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Opik Integration
import opik
from opik.integrations.adk import OpikTracer, track_adk_agent_recursive


# Configure Opik (assumes OPIK_API_KEY is set in environment or local setup)
opik.configure(use_local=False)

# --- Helpers ---

def get_youtube_service():
    """Initializes and returns the YouTube Data API service."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment.")
        return None
    return build('youtube', 'v3', developerKey=api_key)

def parse_iso_duration(duration_str: str) -> int:
    """Parses ISO 8601 duration (PT#M#S) to minutes."""
    try:
        # Simple regex for PT#H#M#S
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            return 20 # Default
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        total_minutes = (hours * 60) + minutes + (1 if seconds >= 30 else 0)
        return total_minutes if total_minutes > 0 else 1
    except Exception:
        return 20

# --- Tools ---

def search_youtube_playlists(trainer_name: str) -> List[Dict[str, Any]]:
    """
    Searches YouTube for playlists by a specific trainer using YouTube Data API.
    Returns a list of playlists with title, id, and thumbnails.
    """
    print(f"Tool called: Searching playlists for {trainer_name}...")
    youtube = get_youtube_service()
    if not youtube:
        print("Error: YouTube service not initialized.")
        return []

    try:
        # Search for playlists
        request = youtube.search().list(
            part="snippet",
            maxResults=15,
            q=f"{trainer_name} workout",
            type="playlist"
        )
        response = request.execute()
        
        playlists = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            playlists.append({
                "title": snippet.get("title"),
                "id": item.get("id", {}).get("playlistId"),
                "link": f"https://www.youtube.com/playlist?list={item.get('id', {}).get('playlistId')}",
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "channel": snippet.get("channelTitle")
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
    
    # 1. Define the tool
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
    
    model = "gemini-2.0-flash"
    agent = Agent(
        name="playlist_curator",
        model=model,
        description="Agent as Fitness Content Curator",
        instruction=system_instruction,
        tools=tools
    )
    
    # Configure Opik tracer
    opik_tracer = OpikTracer(
        name="playlist-curator-agent",
        tags=["seed-script", "curation"],
        metadata={
            "environment": "development",
            "model": model,
            "framework": "google-adk",
        },
        project_name="fitness_coach"
    )
    
    # Recursively track the agent
    track_adk_agent_recursive(agent, opik_tracer)
    
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

async def enrich_workout_metadata(title: str, description: str, duration_str: str) -> Dict[str, Any]:
    """
    Uses Gemini to infer difficulty, equipment, and a clean display title.
    """
    prompt = f"""
    You are a fitness data classifier. Your task is to analyze workout video metadata and infer structured, frontend-ready fields.

    Classify the workout using ONLY the provided information. Do NOT add creativity, opinions, or assumptions beyond the metadata.

    INPUT:
    - Video Title: {title}
    - Description: {description[:500]}
    - Duration (ISO 8601): {duration_str}

    INSTRUCTIONS:

    1. display_title
        - Create a clean, short title (5-7 words).
        - Do NOT copy the YouTube title verbatim.
        - Remove:
            - Trainer names
            - Emojis
            - Marketing language (e.g., "Brutal", "No Repeat", "Insane")
            - Episode numbers
        - Keep:
            - Approximate duration in minutes
            - Workout type or style (e.g., HIIT, Strength, Cardio)
            - Primary focus if clear (e.g., Full Body, Legs, Core)

        Examples:
        - "20 Min HIIT Full Body"
        - "30 Min Dumbbell Legs"
        - "15 Min Low Impact Core"


    2. difficulty_score
        - Integer between 0 and 10.
        - Infer based on:
            - Duration (longer = harder)
            - Intensity indicators (e.g., HIIT, Tabata, AMRAP)
            - Impact level (jumping/plyometrics increase difficulty)
            - Pace and rest structure (minimal rest increases difficulty)
            - External load or resistance
        - Do NOT use trainer reputation or program/series names.

    3. difficulty
        - Must strictly match difficulty_score:
        - 0-2 → "Beginner"
        - 3-6 → "Intermediate"
        - 7-10 → "Advanced"

    
    4. difficulty_reason
        - Array of 2-4 short, concrete reasons.
        - Each reason must reference a specific signal used in scoring.
        - Allowed reason types:
          - Duration-based (e.g., "45+ minute duration")
          - Intensity-based (e.g., "HIIT intervals")
          - Impact-based (e.g., "High impact jumps", "Plyometrics", "Intense trisets", "Slow movements", "Short rest periods")
          - Load-based (e.g., "Weighted exercises", "Body weight only")
          - Equipment-based (e.g., "Dumbbells", "Kettlebell", "Barbell")
        - Avoid vague phrases like "challenging workout" or "high intensity".

    5. equipments
        - Array of required equipment.
        - Normalize names (Title Case, singular or common plural).
        - Examples:
            - "Dumbbells"
            - "Kettlebell"
            - "Barbell"
            - "Resistance Bands"
            - "Yoga Mat"
        - If bodyweight-only, return an empty array [].
        - Do NOT include "None" as a value.

    **Requirements**:
    1. display_title: Clean, short (5-7 words) title. Remove trainer name, emojis, marketing fluff (e.g. "Brutal", "No Repeat"). Keep workout type/focus (e.g. "20 Min HIIT Full Body").
    2. difficulty_score: Integer 0-10 based on duration, intensity (HIIT/Tabata=High), impact, etc.
    3. difficulty: "Beginner" (0-2), "Intermediate" (3-6), or "Advanced" (7-10).
    4. difficulty_reason: Array of 2-4 short strings explaining the score (e.g. "High impact jumps", "Long duration").
    5. equipments: Array of strings (e.g. "Dumbbells", "Kettlebell", "None"). Use "None" if bodyweight only.

    OUTPUT RULES:
    - Return ONLY valid JSON.
    - Do NOT include markdown, comments, or extra text.
    - Ensure all fields are present and correctly typed

    **Output JSON**:
    {{
      "display_title": "string",
      "difficulty_score": int,
      "difficulty": "string",
      "difficulty_reason": ["string"],
      "equipments": ["string"]
    }}
    """
    
    runner = get_runner(
        model_name="gemini-2.0-flash",
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    
    try:
        parts = [types.Part(text=prompt)]
        result_content = await run_agent(runner, parts)
        text_response = extract_text_from_content(result_content)
        return json.loads(text_response)
    except Exception as e:
        print(f"     ! Metadata enrichment failed: {e}")
        # Fallback
        return {
            "display_title": title[:50],
            "difficulty_score": 5,
            "difficulty": "Intermediate",
            "difficulty_reason": ["Default fallback"],
            "equipments": []
        }

async def process_playlist(db, playlist_info, trainer_name, limit_per_playlist=5):
    """
    Fetches videos from a playlist using YouTube Data API.
    """
    playlist_id = playlist_info['id']
    playlist_title = playlist_info['title']
    print(f"  -> Processing Playlist: {playlist_title}")
    
    youtube = get_youtube_service()
    if not youtube:
        return 0

    try:
        # 1. Get Playlist Items (Video IDs)
        # We fetch a bit more than limit to account for private videos etc
        pl_request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=limit_per_playlist + 2 
        )
        pl_response = pl_request.execute()
        
        video_ids = []
        for item in pl_response.get("items", []):
            vid_id = item.get("contentDetails", {}).get("videoId")
            if vid_id:
                video_ids.append(vid_id)
        
        if not video_ids:
            print("     ! No videos found in playlist.")
            return 0
            
        # 2. Get Video Details (Duration, Tags, etc.)
        vid_request = youtube.videos().list(
            part="snippet,contentDetails",
            id=",".join(video_ids[:limit_per_playlist])
        )
        vid_response = vid_request.execute()
        
        collection_ref = db.collection('workout_library')
        count = 0
        
        for video in vid_response.get("items", []):
            try:
                vid_id = video.get("id")
                snippet = video.get("snippet", {})
                content_details = video.get("contentDetails", {})
                
                title = snippet.get("title")
                description = snippet.get("description", "")
                thumbnail_url = snippet.get("thumbnails", {}).get("high", {}).get("url", "")
                
                duration_str = content_details.get("duration", "PT20M")
                duration_mins = parse_iso_duration(duration_str)
                
                focus = infer_focus(title)
                
                # Enrich Metadata (LLM Call)
                print(f"     > Enriching metadata for: {title[:30]}...")
                enriched_data = await enrich_workout_metadata(title, description, duration_str)
                
                doc_id = f"{vid_id}"
                
                workout = {
                    "id": doc_id,
                    "title": title,
                    "trainer": trainer_name,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "duration_mins": duration_mins,
                    "focus": focus,
                    "description": f"From program: {playlist_title}. {title} - {description[:100]}...",
                    "thumbnail": thumbnail_url,
                    "playlist_id": playlist_id,
                    
                    # Enriched Fields
                    "display_title": enriched_data.get("display_title", title),
                    "difficulty": enriched_data.get("difficulty", "Intermediate"),
                    "difficulty_score": enriched_data.get("difficulty_score", 5),
                    "difficulty_reason": enriched_data.get("difficulty_reason", []),
                    "equipments": enriched_data.get("equipments", [])
                }
                
                # Generate Embedding
                text_to_embed = f"""
                    Workout type: {', '.join(workout.get('focus', []))}
                    Trainer: {workout.get('trainer')}
                    Difficulty: {workout.get('difficulty')}
                    Difficulty score: {workout.get('difficulty_score')}
                    Duration: {workout.get('duration_mins')} minutes
                    Equipment: {', '.join(workout.get('equipments', [])) or 'Bodyweight'}
                    """
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
