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

def _strip_duration_terms(text: str) -> str:
    cleaned = re.sub(r'\b\d{1,3}\s*(?:-|to|and)\s*\d{1,3}\s*(?:min|mins|minutes?)?\b', ' ', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b\d{1,3}\s*(?:min|mins|minutes?)\b', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(" ,.-")
    return cleaned

def _extract_desired_focus(message: str) -> List[str]:
    text = (message or "").lower()
    focus: List[str] = []
    if "leg" in text:
        focus.append("legs")
    if "glute" in text:
        focus.append("glutes")
    if "upper body" in text:
        focus.append("upper body")
    if "lower body" in text:
        focus.append("lower body")
    if "core" in text or "abs" in text:
        focus.append("core")
    if "back" in text:
        focus.append("back")
    if "chest" in text:
        focus.append("chest")
    if "bicep" in text:
        focus.append("biceps")
    if "tricep" in text:
        focus.append("triceps")
    if "shoulder" in text:
        focus.append("shoulders")
    if "arm" in text:
        focus.append("arms")
    if "cardio" in text:
        focus.append("cardio")
    if "hiit" in text:
        focus.append("hiit")
    if "full body" in text:
        focus.append("full body")
    if "general fitness" in text:
        focus.append("general fitness")
    seen = set()
    result: List[str] = []
    for f in focus:
        if f not in seen:
            seen.add(f)
            result.append(f)
    return result

def _is_rest_request(message: str) -> bool:
    text = (message or "").lower()
    if "rest day" in text:
        return True
    if "make this a rest" in text:
        return True
    if "make this rest" in text:
        return True
    if "change this to rest" in text:
        return True
    if "skip this" in text:
        return True
    if "no workout" in text:
        return True
    if "off day" in text:
        return True
    if "take a rest" in text:
        return True
    return False

async def build_adjustment_message(
    user_message: str,
    day_index: int,
    current_plan: Dict[str, Any],
    target_day: Dict[str, Any],
    selected_workout: Optional[Dict[str, Any]],
    is_rest: bool,
    max_duration: Optional[int],
    min_duration: Optional[int]
) -> Dict[str, str]:
    instruction = """
    You are a friendly fitness coach assistant.
    You must output ONLY JSON.
    Write a short summary for the UI and a conversational message for the user.
    If the user asked for a rest day and is_rest is true, clearly explain that you are suggesting a rest day and why it makes sense.
    If the proposed workout does not match the requested duration window or focus, briefly explain the mismatch (for example, no workouts under 15 minutes) before suggesting the closest option.
    Do not mention saving or confirming anything; just talk to the user.
    Output:
    {
      "summary": "short summary for the day card",
      "agent_message": "natural language explanation for the chat bubble"
    }
    """
    runner = get_runner(
        model_name="gemini-2.0-flash",
        instruction=instruction,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
        tracer_name="AdjustMessage"
    )
    workout_details = target_day.get("workout_details") or {}
    current_title = target_day.get("activity")
    current_duration = workout_details.get("duration_mins")
    current_focus = workout_details.get("focus")
    proposed_title = None
    proposed_duration = None
    proposed_focus = None
    if selected_workout:
        proposed_title = selected_workout.get("display_title") or selected_workout.get("title")
        proposed_duration = selected_workout.get("duration_mins")
        proposed_focus = selected_workout.get("focus")
    payload = {
        "user_message": user_message,
        "day_index": day_index,
        "weekly_goal": current_plan.get("weekly_focus"),
        "current": {
            "title": current_title,
            "duration_mins": current_duration,
            "focus": current_focus,
        },
        "proposal": {
            "is_rest": is_rest,
            "title": proposed_title if not is_rest else "Rest",
            "duration_mins": proposed_duration if not is_rest else None,
            "focus": proposed_focus if not is_rest else [],
        },
        "constraints": {
            "requested_max_duration": max_duration,
            "requested_min_duration": min_duration,
        },
    }
    prompt = json.dumps(payload)
    try:
        parts = [types.Part(text=prompt)]
        content = await run_agent(runner, parts)
        text_resp = extract_text_from_content(content)
        clean_text = text_resp.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        if isinstance(data, list):
            data = data[0]
        summary = str(data.get("summary") or "Updated workout.")
        agent_message = str(data.get("agent_message") or "Updated your plan.")
        return {"summary": summary, "agent_message": agent_message}
    except Exception:
        if is_rest:
            return {
                "summary": "Marked as rest day.",
                "agent_message": f"You sound tired, so I'm suggesting a rest day for Day {day_index} to help you recover.",
            }
        return {
            "summary": "Updated workout.",
            "agent_message": "Updated your plan with a better fit.",
        }
def _extract_desired_focus(message: str) -> List[str]:
    text = (message or "").lower()
    focus: List[str] = []
    if "leg" in text:
        focus.append("legs")
    if "glute" in text:
        focus.append("glutes")
    if "upper body" in text:
        focus.append("upper body")
    if "lower body" in text:
        focus.append("lower body")
    if "core" in text or "abs" in text:
        focus.append("core")
    if "back" in text:
        focus.append("back")
    if "chest" in text:
        focus.append("chest")
    if "bicep" in text:
        focus.append("biceps")
    if "tricep" in text:
        focus.append("triceps")
    if "shoulder" in text:
        focus.append("shoulders")
    if "arm" in text:
        focus.append("arms")
    if "cardio" in text:
        focus.append("cardio")
    if "hiit" in text:
        focus.append("hiit")
    if "full body" in text:
        focus.append("full body")
    if "general fitness" in text:
        focus.append("general fitness")
    # Deduplicate while preserving order
    seen = set()
    result: List[str] = []
    for f in focus:
        if f not in seen:
            seen.add(f)
            result.append(f)
    return result

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

def _select_best_candidate_relaxed(
    candidates: List[Dict[str, Any]],
    existing_ids: List[str],
    prev_focus: List[str],
    next_focus: List[str],
    target_focus: List[str]
) -> Optional[Dict[str, Any]]:
    cleaned = []
    for c in candidates:
        workout_id = c.get("id")
        if not workout_id or str(workout_id).startswith("fallback"):
            continue
        if workout_id in existing_ids:
            continue
        cleaned.append(c)
    if not cleaned:
        return None
    prev_set = set([f.lower() for f in prev_focus or []])
    next_set = set([f.lower() for f in next_focus or []])
    target_set = set([f.lower() for f in target_focus or []])

    def norm_focus(cand: Dict[str, Any]) -> List[str]:
        values = cand.get("focus", []) or []
        if isinstance(values, list):
            return [str(f).lower() for f in values]
        if isinstance(values, str):
            return [values.lower()]
        return []

    def sort_by_duration(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            items,
            key=lambda x: x.get("duration_mins") if isinstance(x.get("duration_mins"), (int, float)) else 10**9
        )

    def avoid_adjacent(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for c in items:
            focus = set(norm_focus(c))
            if prev_set.intersection(focus) or next_set.intersection(focus):
                continue
            result.append(c)
        return result

    same_focus = [c for c in cleaned if target_set.intersection(norm_focus(c))]
    same_focus_no_adj = avoid_adjacent(same_focus)
    any_no_adj = avoid_adjacent(cleaned)

    if same_focus_no_adj:
        return sort_by_duration(same_focus_no_adj)[0]
    if same_focus:
        return sort_by_duration(same_focus)[0]
    if any_no_adj:
        return sort_by_duration(any_no_adj)[0]
    return sort_by_duration(cleaned)[0]

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
    current_focus = workout_details.get("focus") or []
    desired_focus = _extract_desired_focus(user_message)
    target_focus = desired_focus or current_focus
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
    if _is_rest_request(user_message):
        message_data = await build_adjustment_message(
            user_message,
            day_index,
            current_plan,
            target_day,
            None,
            True,
            max_duration,
            min_duration,
        )
        return {
            "success": True,
            "new_workout_id": None,
            "new_activity_title": "Rest",
            "is_rest": True,
            "summary": message_data["summary"],
            "agent_response": message_data["agent_message"],
            "selected_workout": None,
            "requested_max_duration": max_duration,
            "requested_min_duration": min_duration,
        }
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
    if query_text:
        query_text = _strip_duration_terms(query_text)
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
    if selected and target_focus and max_duration is None and min_duration is None:
        raw_focus = selected.get("focus") or []
        if isinstance(raw_focus, list):
            sel_focus = [str(f).lower() for f in raw_focus]
        elif isinstance(raw_focus, str):
            sel_focus = [raw_focus.lower()]
        else:
            sel_focus = []
        target_set = set([str(f).lower() for f in (target_focus or [])])
        if not target_set.intersection(sel_focus):
            alt = _select_best_candidate_relaxed(
                candidates,
                existing_ids,
                prev_focus,
                next_focus,
                target_focus
            )
            if alt:
                selected = alt
    if not selected and (max_duration is not None or min_duration is not None):
        print("[Adjust] relaxing duration constraints")
        selected = _select_best_candidate_relaxed(
            candidates,
            existing_ids,
            prev_focus,
            next_focus,
            target_focus
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
        message_data = await build_adjustment_message(
            user_message,
            day_index,
            current_plan,
            target_day,
            None,
            True,
            max_duration,
            min_duration,
        )
        return {
            "success": True,
            "new_workout_id": None,
            "new_activity_title": "Rest",
            "is_rest": True,
            "summary": message_data["summary"],
            "agent_response": message_data["agent_message"],
            "selected_workout": None,
            "requested_max_duration": max_duration,
            "requested_min_duration": min_duration,
        }
    selected["thumbnail"] = _normalize_media_url(selected.get("thumbnail"))
    selected["url"] = _normalize_media_url(selected.get("url"))
    activity_title = selected.get("display_title") or selected.get("title")
    message_data = await build_adjustment_message(
        user_message,
        day_index,
        current_plan,
        target_day,
        selected,
        False,
        max_duration,
        min_duration,
    )
    return {
        "success": True,
        "new_workout_id": selected.get("id"),
        "new_activity_title": activity_title,
        "is_rest": False,
        "summary": message_data["summary"],
        "agent_response": message_data["agent_message"],
        "selected_workout": selected,
        "requested_max_duration": max_duration,
        "requested_min_duration": min_duration,
    }
