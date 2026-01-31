from google import genai
from google.genai import types
from backend.core.config import settings
import json
import base64

def check_ai_connection():
    status = {
        "initialized": False,
        "api_key_present": False,
        "connectivity": "unknown",
        "error": None
    }
    
    if not settings.GOOGLE_API_KEY:
        status["error"] = "GOOGLE_API_KEY not found in environment variables"
        return status
        
    status["api_key_present"] = True
    
    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        # Simple test to list models or generate a tiny content
        # Listing models is a good connectivity check
        # We'll iterate to get just one model to verify access
        models_iter = client.models.list()
        first_model = next(models_iter, None)
        
        status["initialized"] = True
        status["connectivity"] = "connected"
        status["details"] = f"Successfully connected. Found model: {first_model.name if first_model else 'None'}"
        
    except Exception as e:
        status["connectivity"] = "failed"
        status["error"] = str(e)
        
    return status

def _get_client():
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set")
    return genai.Client(api_key=settings.GOOGLE_API_KEY)

def analyze_body_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    client = _get_client()
    
    prompt = """
    You are an expert fitness coach. Analyze this body photo to estimate a high-level body category.
    Category Definitions:
    - Lean: Clearly visible muscle definition, low body fat.
    - Average: Moderate body fat, some muscle definition, healthy appearance.
    - Overfat: Higher body fat percentage, limited muscle visibility.
    
    Output JSON with 'category' (Lean|Average|Overfat) and 'reasoning'.
    Do NOT provide medical advice.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_bytes)),
                    types.Part(text=prompt)
                ]
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    try:
        return json.loads(response.text)
    except Exception as e:
        return {"category": "Unknown", "reasoning": f"Failed to parse AI response: {response.text}"}

def _decode_inline_data(data: object) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return base64.b64decode(data)
    raise ValueError("Unsupported inline data format from model response")

def _extract_image_from_response(response) -> bytes:
    if not response or not getattr(response, "candidates", None):
        raise ValueError("Model returned no candidates")
    for candidate in response.candidates:
        content = getattr(candidate, "content", None)
        if not content or not getattr(content, "parts", None):
            continue
        for part in content.parts:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                return _decode_inline_data(inline.data)
    raise ValueError("Model returned no image data")

def generate_future_physique(image_bytes: bytes, goal_key: str, mime_type: str = "image/jpeg") -> bytes:
    client = _get_client()
    
    # Goal prompts map
    goals = {
        "lean": "a Lean & Toned physique. Target 8-10% body fat. Visible six-pack abs, defined oblique muscles, tight waist. No excess fat. The look of a calisthenics athlete or boxer. Sharp definition.",
        "athletic": "a Fit & Athletic physique. Broad shoulders, V-shaped torso, flat stomach with visible muscle tone. Well-developed chest and arms. The look of a competitive swimmer or decathlete. Healthy, capable, and strong, but not overly bulky.",
        "muscle": "a Muscular & Powerful physique. Significant natural muscle mass. Large chest, thick arms, and strong legs. Target 12-15% body fat (visible abs but not shredded). The look of a superhero actor or rugby player. Impressive size but realistic proportions."
    }
    
    goal_desc = goals.get(goal_key, "healthy physique")
    prompt = (
        f"Transform the person in the reference photo to have {goal_desc}. "
        "Maintain the person's face, skin tone, and head to preserve identity, but completely modify the body shape to match the target physique. "
        "Keep the same standing pose, framing, lighting, and background. "
        "Generate a photorealistic, high-quality, 8k image. Ensure the body looks natural and not cartoonish."
    )
    
    response = client.models.generate_content(
        model="gemini-2.5-flash-image", # Using flash-exp which often supports generation in preview
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=image_bytes,
                        )
                    ),
                    types.Part(text=prompt),
                ],
            )
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )
    return _extract_image_from_response(response)

def recommend_fitness_path(
    original_image_bytes: bytes,
    lean_image_bytes: bytes,
    athletic_image_bytes: bytes,
    muscle_image_bytes: bytes,
    mime_type: str = "image/jpeg"
) -> dict:
    client = _get_client()
    
    prompt = """
    You are an expert fitness coach helping a user choose a transformation path.
    
    I will provide 4 images:
    1. The user's current physique (Original)
    2. A potential 'Lean & Toned' future self (Lean)
    3. A potential 'Athletic Build' future self (Athletic)
    4. A potential 'Muscle Gain' future self (Muscle)
    
    Your task:
    Analyze the gap between the current state and each goal. Provide a realistic assessment.
    
    Output structured JSON:
    {
      "lean": {
         "time_estimate": "X-Y months",
         "effort_level": "Moderate/High/Extreme",
         "description": "Short explanation..."
      },
      "athletic": {
         "time_estimate": "X-Y months",
         "effort_level": "Moderate/High/Extreme",
         "description": "Short explanation..."
      },
      "muscle": {
         "time_estimate": "X-Y months",
         "effort_level": "Moderate/High/Extreme",
         "description": "Short explanation..."
      },
      "recommendation": {
         "suggested_path": "lean" | "athletic" | "muscle",
         "reasoning": "Why this is the best starting point..."
      }
    }
    
    Do NOT provide medical advice. Be realistic about natural transformation timelines.
    """
    
    # Parts order matches the prompt description
    parts = [
        types.Part(text=prompt),
        types.Part(text="Original Image:"),
        types.Part(inline_data=types.Blob(mime_type=mime_type, data=original_image_bytes)),
        types.Part(text="Lean Goal:"),
        types.Part(inline_data=types.Blob(mime_type=mime_type, data=lean_image_bytes)),
        types.Part(text="Athletic Goal:"),
        types.Part(inline_data=types.Blob(mime_type=mime_type, data=athletic_image_bytes)),
        types.Part(text="Muscle Goal:"),
        types.Part(inline_data=types.Blob(mime_type=mime_type, data=muscle_image_bytes)),
    ]
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    try:
        return json.loads(response.text)
    except Exception as e:
        return {
            "error": "Failed to parse AI response", 
            "raw_text": response.text,
            "recommendation": {
                "suggested_path": "lean", 
                "reasoning": "Default fallback due to parsing error."
            }
        }

def generate_text_embedding(text: str) -> list:
    """Generates a text embedding vector for the given text."""
    client = _get_client()
    try:
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return []

def generate_weekly_plan_rag(user_goal: str, available_workouts: list) -> dict:
    """
    Generates a 1-week workout plan using retrieved workouts.
    
    Args:
        user_goal: 'lean', 'athletic', or 'muscle'
        available_workouts: List of workout dicts (id, title, focus, etc.)
        
    Returns:
        JSON dict with weekly schedule.
    """
    client = _get_client()
    
    # Simplify workout list for the prompt to save tokens
    workouts_context = []
    for w in available_workouts:
        workouts_context.append(f"ID: {w['id']} | Title: {w['title']} | Focus: {', '.join(w.get('focus', []))} | Difficulty: {w.get('difficulty', 'N/A')}")
    
    workouts_str = "\n".join(workouts_context)
    
    prompt = f"""
    You are an expert fitness coach creating a 1-week workout plan for a client.
    
    **Client Goal**: {user_goal.upper()}
    
    **Available Workout Library** (Caroline Girvan):
    {workouts_str}
    
    **Instructions**:
    1. Create a 7-day schedule (Monday to Sunday).
    2. Select the MOST appropriate workouts from the library for the goal '{user_goal}'.
    3. You can repeat workouts if necessary, but try to balance the week.
    4. Include 1 or 2 Rest Days or Active Recovery days (using the Stretch video if applicable).
    5. For 'Muscle', prioritize Hypertrophy/Strength. For 'Lean', prioritize HIIT/Full Body.
    
    **Output Format**:
    Return ONLY valid JSON with this structure:
    {{
      "weekly_focus": "Brief summary of the week's intent",
      "schedule": [
        {{
          "day": 1,
          "day_name": "Monday",
          "workout_id": "id_from_library", 
          "activity": "Title or Description",
          "is_rest": false,
          "notes": "Why this workout?"
        }},
        ... (days 2-7)
      ]
    }}
    If a day is a REST day, set "workout_id": null and "is_rest": true.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Plan generation failed: {e}")
        # Fallback simple plan
        return {
            "weekly_focus": "General Fitness (Fallback)",
            "schedule": [{"day": i, "day_name": d, "is_rest": True, "workout_id": None, "activity": "Rest"} for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], 1)]
        }


