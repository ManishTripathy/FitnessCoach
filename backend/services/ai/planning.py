import json
from google.genai import types
from backend.services.ai.core import get_runner, run_agent, extract_text_from_content

async def generate_weekly_plan_rag(user_goal: str, available_workouts: list) -> dict:
    """
    Generates a 1-week workout plan using retrieved workouts.
    """
    
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
        print(f"Plan generation failed: {e}")
        # Fallback simple plan
        return {
            "weekly_focus": "General Fitness (Fallback)",
            "schedule": [{"day": i, "day_name": d, "is_rest": True, "workout_id": None, "activity": "Rest"} for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], 1)]
        }
