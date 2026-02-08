import json
from google.genai import types
from backend.services.ai.core import get_runner, run_agent, extract_text_from_content

async def recommend_fitness_path(
    original_image_bytes: bytes,
    lean_image_bytes: bytes,
    athletic_image_bytes: bytes,
    muscle_image_bytes: bytes,
    mime_type: str = "image/jpeg"
) -> dict:
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
         "reasoning": "Why this is the best starting point...",
         "confidence_score": 0.0 to 1.0
      }
    }
    
    Do NOT provide medical advice. Be realistic about natural transformation timelines.
    """
    
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
    
    runner = get_runner(
        model_name="gemini-2.0-flash",
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    
    try:
        result_content = await run_agent(runner, parts)
        text_response = extract_text_from_content(result_content)
        return json.loads(text_response)
    except Exception as e:
        return {
            "error": "Failed to parse AI response", 
            "raw_text": str(e),
            "recommendation": {
                "suggested_path": "lean", 
                "reasoning": "Default fallback due to parsing error."
            }
        }
