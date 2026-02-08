import json
from typing import List, Dict, Any
from google.genai import types
from backend.services.ai.core import get_runner, run_agent, extract_text_from_content

async def detect_intent(message: str, context: Dict[str, Any]) -> str:
    """
    Classifies the user's intent based on the message and context.
    Returns: 'ADJUST_WORKOUT', 'EXPLAIN_WORKOUT', 'MOTIVATION', or 'UNKNOWN'
    """
    prompt = f"""
    You are an intent classifier for a fitness coach AI.
    
    User Message: "{message}"
    Context: User is viewing Day {context.get('day_index', '?')} of their workout plan.
    Current Workout: {context.get('workout_title', 'Unknown')}
    
    Classify the intent into one of these categories:
    - ADJUST_WORKOUT: User wants to change duration, difficulty, or swap the workout (e.g., "too hard", "only have 20 mins", "change this").
    - EXPLAIN_WORKOUT: User asks about the workout details (e.g., "what is this?", "how to do pushups").
    - MOTIVATION: User seeks encouragement.
    - OTHER: Anything else.
    
    Output ONLY the category name.
    """
    
    runner = get_runner(model_name="gemini-2.0-flash")
    parts = [types.Part(text=prompt)]
    
    try:
        content = await run_agent(runner, parts)
        intent = extract_text_from_content(content).strip().upper()
        # Basic cleanup
        if "ADJUST" in intent: return "ADJUST_WORKOUT"
        if "EXPLAIN" in intent: return "EXPLAIN_WORKOUT"
        if "MOTIVATION" in intent: return "MOTIVATION"
        return "OTHER"
    except Exception:
        return "OTHER"

async def adjust_workout(
    user_message: str, 
    day_index: int, 
    current_plan: Dict[str, Any], 
    available_workouts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Adjusts the workout for a specific day based on user constraints.
    Returns a dict with:
    - updated_day: The new day object
    - summary: A short summary of changes
    - agent_response: A conversational response
    """
    
    # Contextualize the request
    # Flatten available workouts for context (assuming < 50 items, fits in context)
    workouts_str = "\n".join([
        f"ID: {w['id']} | Title: {w['title']} | Duration: {w.get('duration_mins','?')} | Focus: {w.get('focus',[])} | Difficulty: {w.get('difficulty','?')}"
        for w in available_workouts
    ])
    
    target_day = next((d for d in current_plan.get('schedule', []) if d['day'] == day_index), None)
    if not target_day:
        return {
            "error": "Day not found",
            "agent_response": "I couldn't find that day in your plan."
        }

    prompt = f"""
    You are an expert fitness coach. A user wants to modify their workout for Day {day_index}.
    
    **Current Plan Context**:
    - Goal: {current_plan.get('weekly_focus', 'General Fitness')}
    - Day {day_index} Current Workout: {target_day.get('activity', 'Rest')} (ID: {target_day.get('workout_id', 'None')})
    
    **User Request**: "{user_message}"
    
    **Available Workouts**:
    {workouts_str}
    
    **Instructions**:
    1. Select the BEST alternative workout from the list that meets the user's need (e.g., shorter duration, lower intensity).
    2. If the user wants a rest day, set workout_id to null and is_rest to true.
    3. Ensure the new workout still fits reasonably within the weekly goal if possible.
    
    **Output JSON**:
    {{
      "new_workout_id": "id_from_library" (or null if rest),
      "new_activity_title": "Title",
      "is_rest": boolean,
      "reasoning_summary": "Short concise summary for UI (e.g. 'Switched to 20-min HIIT')",
      "agent_message": "Conversational response to user (e.g. 'No problem! I've swapped it for a shorter session.')"
    }}
    """
    
    runner = get_runner(
        model_name="gemini-2.0-flash",
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    
    try:
        parts = [types.Part(text=prompt)]
        content = await run_agent(runner, parts)
        text_resp = extract_text_from_content(content)
        result = json.loads(text_resp)
        
        # Construct the response
        return {
            "success": True,
            "new_workout_id": result.get("new_workout_id"),
            "new_activity_title": result.get("new_activity_title"),
            "is_rest": result.get("is_rest", False),
            "summary": result.get("reasoning_summary", "Updated workout."),
            "agent_response": result.get("agent_message", "Updated your plan.")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "agent_response": "I had trouble adjusting the plan. Please try again."
        }
