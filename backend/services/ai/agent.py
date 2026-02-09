import json
import re
import uuid
from typing import List, Dict, Any, Optional
from google.genai import types
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from backend.services.ai.core import get_runner, run_agent, extract_text_from_content
from backend.services.ai.planning import search_workouts_tool

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

def _normalize_media_url(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    return value.strip().strip("`")

async def detect_intent_multi_agent(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    instruction = """
    You are an intent classifier for a fitness coach AI.
    You must output ONLY JSON.
    Classify the intent into one of these categories:
    - ADJUST_WORKOUT: User wants to change duration, difficulty, or swap the workout.
      Examples: "too hard", "only have 20 mins", "change this", "Between 10 to 15 mins please", "shorter", "longer".
    - EXPLAIN_WORKOUT: User asks about the workout details or technique.
      Examples: "what is this?", "how to do pushups", "explain the focus".
    - MOTIVATION: User seeks encouragement.
    - OTHER: Anything else.

    Output JSON:
    {
      "intent": "ADJUST_WORKOUT|EXPLAIN_WORKOUT|MOTIVATION|OTHER"
    }
    """
    
    runner = get_runner(
        model_name="gemini-2.0-flash",
        instruction=instruction,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
        tracer_name="IntentDetector"
    )
    
    prompt = f"""
    User Message: "{message}"
    Context: Day {context.get('day_index', '?')}
    Current Workout: {context.get('workout_title', 'Unknown')}
    Current Duration (mins): {context.get('current_duration_mins')}
    Current Focus: {context.get('current_focus')}
    """
    
    try:
        parts = [types.Part(text=prompt)]
        content = await run_agent(runner, parts)
        text_resp = extract_text_from_content(content)
        clean_text = text_resp.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_text)
        if isinstance(result, list):
            result = result[0]
        return result
    except Exception:
        return {"intent": "OTHER"}

def _parse_duration_request(message: str, current_duration: Optional[int]) -> Dict[str, Optional[int]]:
    text = (message or "").lower()
    
    # 1. Check for range: "35-40 mins", "35 to 40 mins", "between 35 and 40 mins"
    # Matches: "35-40", "35 to 40", "35 and 40" (if preceded by between)
    range_match = re.search(r'(\d{1,3})\s*(?:-|to|and)\s*(\d{1,3})\s*(?:min|mins|minutes)', text)
    if range_match:
        v1 = int(range_match.group(1))
        v2 = int(range_match.group(2))
        return {"max_duration": max(v1, v2), "min_duration": min(v1, v2)}

    # 2. Check for explicit max: "under 30", "less than 30", "max 30", "up to 30"
    max_match = re.search(r'(?:under|less than|max|up to|<)\s*(\d{1,3})', text)
    if max_match:
        return {"max_duration": int(max_match.group(1)), "min_duration": None}

    # 3. Check for explicit min: "over 30", "more than 30", "min 30", "at least 30"
    min_match = re.search(r'(?:over|more than|min|at least|>)\s*(\d{1,3})', text)
    if min_match:
        return {"max_duration": None, "min_duration": int(min_match.group(1))}

    # 4. Fallback: "30 mins" (treat as max duration, assuming user has limited time)
    match = re.search(r'(\d{1,3})\s*(?:min|mins|minutes)', text)
    if match:
        return {"max_duration": int(match.group(1)), "min_duration": None}

    # 5. Relative keywords
    if any(k in text for k in ["shorter", "less time", "quick", "faster", "shorten"]):
        if current_duration:
            return {"max_duration": max(5, current_duration - 5), "min_duration": None}
    if any(k in text for k in ["longer", "more time", "extended"]):
        if current_duration:
            return {"max_duration": None, "min_duration": current_duration + 5}

    return {"max_duration": None, "min_duration": None}

def _select_best_candidate(
    candidates: List[Dict[str, Any]],
    existing_ids: List[str],
    prev_focus: List[str],
    next_focus: List[str],
    max_duration: Optional[int],
    min_duration: Optional[int]
) -> Optional[Dict[str, Any]]:
    filtered = []
    for c in candidates:
        workout_id = c.get("id")
        if not workout_id or str(workout_id).startswith("fallback"):
            continue
        if workout_id in existing_ids:
            continue
        duration = c.get("duration_mins")
        if max_duration is not None and isinstance(duration, (int, float)) and duration > max_duration:
            continue
        if min_duration is not None and isinstance(duration, (int, float)) and duration < min_duration:
            continue
        filtered.append(c)
    if not filtered:
        return None
    prev_set = set([f.lower() for f in prev_focus or []])
    next_set = set([f.lower() for f in next_focus or []])
    for c in filtered:
        focus = [f.lower() for f in c.get("focus", []) or []]
        if prev_set.intersection(focus) or next_set.intersection(focus):
            continue
        return c
    return filtered[0]

async def build_semantic_query_agent(
    user_message: str,
    intent: str,
    current_plan: Dict[str, Any],
    target_day: Dict[str, Any],
    day_index: int,
    max_duration: Optional[int],
    min_duration: Optional[int],
    prev_focus: List[str],
    next_focus: List[str]
) -> str:
    instruction = """
    You create a single semantic search query for a workout database.
    You must output ONLY JSON.
    Use this embedding format as guidance:
    Workout type: <focus>
    Trainer: <trainer>
    Difficulty: <difficulty>
    Difficulty score: <score>
    Duration: <minutes> minutes
    Equipment: <equipment list or Bodyweight>

    Build a concise query that includes:
    - desired focus or workout type
    - duration constraint if provided
    - equipment if relevant
    - avoid repeating adjacent day focus when possible

    Output JSON:
    { "query": "<one-line query>" }
    """
    
    runner = get_runner(
        model_name="gemini-2.0-flash",
        instruction=instruction,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
        tracer_name="SemanticQueryBuilder"
    )

    workout_details = target_day.get("workout_details") or {}
    prompt = f"""
    User Message: "{user_message}"
    Intent: {intent}
    Weekly Goal: {current_plan.get('weekly_focus')}
    Day To Adjust: {day_index}
    Current Workout Title: {target_day.get('activity')}
    Current Focus: {workout_details.get('focus')}
    Current Duration: {workout_details.get('duration_mins')}
    Current Equipment: {workout_details.get('equipments')}
    Adjacent Day Focus: {json.dumps({"prev": prev_focus, "next": next_focus})}
    Duration Constraint: max={max_duration}, min={min_duration}
    """
    
    try:
        parts = [types.Part(text=prompt)]
        content = await run_agent(runner, parts)
        text_resp = extract_text_from_content(content)
        clean_text = text_resp.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_text)
        if isinstance(result, list):
            result = result[0]
        return str(result.get("query", "")).strip()
    except Exception:
        return ""

async def adjust_workout_multi_agent(
    user_message: str,
    day_index: int,
    current_plan: Dict[str, Any],
    intent_data: Dict[str, Any]
) -> Dict[str, Any]:
    target_day = next((d for d in current_plan.get("schedule", []) if d["day"] == day_index), None)
    if not target_day:
        return {
            "success": False,
            "error": "Day not found",
            "agent_response": "I couldn't find that day in your plan."
        }
    workout_details = target_day.get("workout_details") or {}
    current_duration = workout_details.get("duration_mins")
    existing_ids = [
        d.get("workout_id") for d in current_plan.get("schedule", [])
        if d.get("workout_id") and d.get("day") != day_index
    ]
    prev_day = next((d for d in current_plan.get("schedule", []) if d.get("day") == day_index - 1), None)
    next_day = next((d for d in current_plan.get("schedule", []) if d.get("day") == day_index + 1), None)
    prev_focus = (prev_day or {}).get("workout_details", {}).get("focus", [])
    next_focus = (next_day or {}).get("workout_details", {}).get("focus", [])
    intent = str(intent_data.get("intent", "OTHER")).upper()
    durations = _parse_duration_request(user_message, current_duration)
    max_duration = durations.get("max_duration")
    min_duration = durations.get("min_duration")
    query_text = await build_semantic_query_agent(
        user_message,
        intent,
        current_plan,
        target_day,
        day_index,
        max_duration,
        min_duration,
        prev_focus,
        next_focus
    )
    print(f"[Adjust] intent={intent} day={day_index} current_duration={current_duration} max={max_duration} min={min_duration}")
    print(f"[Adjust] query={query_text}")
    results_json = search_workouts_tool(
        query=query_text or target_day.get("activity") or "",
        max_duration=max_duration,
        min_duration=min_duration
    )
    try:
        candidates = json.loads(results_json)
    except Exception:
        candidates = []
    if not isinstance(candidates, list):
        candidates = []
    print(f"[Adjust] candidates_count={len(candidates)}")
    selected = _select_best_candidate(
        candidates,
        existing_ids,
        prev_focus,
        next_focus,
        max_duration,
        min_duration
    )
    if not selected and (max_duration is not None or min_duration is not None):
        print("[Adjust] relaxing duration constraints")
        selected = _select_best_candidate(
            candidates,
            existing_ids,
            prev_focus,
            next_focus,
            None,
            None
        )
    if not selected and candidates:
        print("[Adjust] relaxing focus constraints")
        selected = _select_best_candidate(
            candidates,
            existing_ids,
            [],
            [],
            None,
            None
        )
    if not selected:
        return {
            "success": True,
            "new_workout_id": None,
            "new_activity_title": "Rest",
            "is_rest": True,
            "summary": "Marked as rest day.",
            "agent_response": "I couldn't find a suitable match, so I set this as a rest day.",
            "selected_workout": None
        }
    selected["thumbnail"] = _normalize_media_url(selected.get("thumbnail"))
    selected["url"] = _normalize_media_url(selected.get("url"))
    activity_title = selected.get("display_title") or selected.get("title")
    summary = "Updated workout."
    if max_duration:
        summary = f"Switched to a shorter workout (~{selected.get('duration_mins')} min)."
    elif min_duration:
        summary = f"Switched to a longer workout (~{selected.get('duration_mins')} min)."
    return {
        "success": True,
        "new_workout_id": selected.get("id"),
        "new_activity_title": activity_title,
        "is_rest": False,
        "summary": summary,
        "agent_response": "Updated your plan with a better fit.",
        "selected_workout": selected
    }
