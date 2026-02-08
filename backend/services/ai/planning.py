import json
import asyncio
import uuid
import datetime
from typing import List, Dict, Any, Optional

from google.genai import types
from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models import Gemini

from backend.services.ai.core import get_runner, run_agent, extract_text_from_content, check_ai_connection
from backend.services.ai.embedding import generate_text_embedding
from backend.services.firebase_service import get_db
from opik.integrations.adk import OpikTracer, track_adk_agent_recursive
import opik

# Configure Opik
opik.configure(use_local=False)
opik_tracer = OpikTracer(
    name="fitness-planner-pipeline",
    tags=["planning", "rag", "multi-agent"],
    project_name="fitness_coach"
)

# --- Tools ---

def search_workouts_tool(query: str) -> str:
    """
    Searches for workouts using semantic vector search against the workout library.
    
    Args:
        query: The search query description (e.g. "high intensity leg workout").
        
    Returns:
        JSON string list of matching workouts with details (id, title, focus, difficulty).
    """
    import sys
    print(f"[Tool] Searching workouts for: '{query}'", file=sys.stderr)
    print(f"[Tool] Searching workouts for: '{query}'")
    
    db = get_db()
    if not db:
        print("[Tool] Database connection failed.")
        return json.dumps([{"id": "fallback_db_error", "title": "Rest or Stretch (System Error)", "focus": ["Recovery"], "difficulty": "Beginner"}])
    
    text_to_embed = f"{query}"
    # Remove focus parameter logic
    
    query_embedding = generate_text_embedding(text_to_embed)
    
    if not query_embedding:
        print("[Tool] Embedding generation failed.")
        return json.dumps([{"id": "fallback_embedding_error", "title": "Rest or Stretch (AI Error)", "focus": ["Recovery"], "difficulty": "Beginner"}])
        
    try:
        collection = db.collection('workout_library')
        
        # Use vector search
        from google.cloud.firestore_v1.vector import Vector
        from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
        
        # We assume the 'embedding' field exists and is indexed
        print(f"[Tool] Executing vector query with dim={len(query_embedding)}...")
        vector_query = collection.find_nearest(
            vector_field="embedding",
            query_vector=Vector(query_embedding),
            distance_measure=DistanceMeasure.COSINE,
            limit=3  # Fetch top 3 to give the agent options
        )
        
        results = vector_query.get()
        print(f"[Tool] Vector query returned {len(results)} results.")
        
        workouts = []
        for doc in results:
            data = doc.to_dict()
            # Clean up data for the agent
            workout_clean = {
                "id": data.get("id"),
                "title": data.get("title"),
                "display_title": data.get("display_title", data.get("title")),
                "focus": data.get("focus", []),
                "difficulty": data.get("difficulty"),
                "difficulty_score": data.get("difficulty_score"),
                "difficulty_reason": data.get("difficulty_reason", []),
                "duration_mins": data.get("duration_mins"),
                "equipments": data.get("equipments", []),
                "thumbnail": data.get("thumbnail"),
                "url": data.get("url"),
                "trainer": data.get("trainer"),
                "playlist_id": data.get("playlist_id"),
                "description": (data.get("description", "") or "")[:200]
            }
            workouts.append(workout_clean)
            
        if not workouts:
             return json.dumps([{"id": "fallback", "title": "Rest or Stretch", "focus": ["Recovery"], "difficulty": "Beginner"}])

        print(f"[Tool] Found {len(workouts)} workouts for query: '{query}'")
        print(f"[Tool] Workouts: {workouts}")

        return json.dumps(workouts)
        
    except Exception as e:
        print(f"[Tool] Vector search failed: {e}")
        return json.dumps([{"id": "fallback_exception", "title": "Rest or Stretch (Search Error)", "focus": ["Recovery"], "difficulty": "Beginner"}])

# --- Agents ---

# 1. Skeleton Generator
skeleton_agent = Agent(
    name="SkeletonGenerator",
    model="gemini-2.0-flash",
    instruction="""
    You are an expert fitness planner.
    Your task is to create a WEEKLY WORKOUT SKELETON based on the user's goal.
    
    For each day (1-7), determine:
    1. The primary Focus (e.g., Legs, Upper Body, HIIT, Rest, Active Recovery).
    2. A specific Search Query to find the perfect workout for this day.
    
    Consider:
    - Balance: Don't work the same muscle group two days in a row (unless split properly).
    - Recovery: Include 1-2 rest/recovery days.
    - Goal Specificity: 
      - "Build Muscle": Focus on splits (Push/Pull/Legs) or Upper/Lower.
      - "Lose Weight": Focus on HIIT, Full Body, Cardio.
      - "Endurance": Focus on longer duration, cardio.
    
    Output Format:
    Return a JSON object:
    {
      "weekly_goal": "...",
      "days": [
        {"day": 1, "focus": "...", "search_query": "..."},
        ...
      ]
    }
    """,
    output_key="skeleton",
    # before_agent_callback=opik_tracer.before_agent_callback,
    # after_agent_callback=opik_tracer.after_agent_callback,
    # before_model_callback=opik_tracer.before_model_callback,
    # after_model_callback=opik_tracer.after_model_callback
)

# 2. Retrieval Specialist
retrieval_agent = Agent(
    name="RetrievalSpecialist",
    model="gemini-2.0-flash",
    instruction="""
    You are a Workout Retrieval Specialist.
    You will receive a Weekly Skeleton (check session state 'skeleton').
    
    CRITICAL INSTRUCTION: You DO NOT have internal knowledge of specific workouts. You MUST use the `search_workouts_tool` to find them.
    
    Your task:
    1. Parse the skeleton from session state 'skeleton'.
    2. For EACH day in the skeleton that is NOT a Rest day:
       - Formulate a detailed search query including activity and focus (e.g. "High intensity leg workout for mass").
       - Call the `search_workouts_tool` with this `query`.
       - From the results, Select the BEST single workout that fits the flow.
       - You MUST use the actual 'id' returned by the tool. DO NOT invent IDs.
       - If the tool returns a fallback workout (id starts with 'fallback'), use it or mark the day as Rest.
       - You MUST include the 'url' and 'thumbnail' fields in the selected_workout object exactly as returned by the tool.
    3. For Rest days, explicitly set activity to "Rest" or "Active Recovery".
    
    Output Format:
    Return a JSON object with the selected workouts:
    {
       "schedule": [
          {"day": 1, "focus": "...", "selected_workout": { "id": "...", "title": "...", "url": "...", "thumbnail": "...", ... } or null},
          ...
       ]
    }
    """,
    tools=[search_workouts_tool],
    output_key="retrieved_plan",
    # before_agent_callback=opik_tracer.before_agent_callback,
    # after_agent_callback=opik_tracer.after_agent_callback,
    # before_model_callback=opik_tracer.before_model_callback,
    # after_model_callback=opik_tracer.after_model_callback,
    # before_tool_callback=opik_tracer.before_tool_callback,
    # after_tool_callback=opik_tracer.after_tool_callback
)

# 3. Plan Assembler
assembler_agent = Agent(
    name="PlanAssembler",
    model="gemini-2.0-flash",
    instruction="""
    You are the Final Plan Assembler.
    You will receive a schedule with selected workouts in the prompt below.
    
    Your task:
    1. Review the plan for coherence.
    2. Add a "notes" field to each day explaining WHY this workout fits the flow.
    3. Ensure the format matches the strict frontend requirement.
    4. CRITICAL: For each day with a workout, you MUST preserve the 'workout_id' from the `retrieved_plan` exactly. Do not change it.
    5. CRITICAL: Do NOT write any code (Python, etc.). Output ONLY valid JSON.
    
    Frontend Output Format (Strict JSON):
    {
      "weekly_focus": "Summary of the week",
      "schedule": [
        {
          "day": 1,
          "day_name": "Monday", (or Tuesday, etc.)
          "workout_id": "...", (or null for Rest)
          "activity": "Display Title",
          "is_rest": boolean,
          "notes": "..."
        },
        ...
      ]
    }
    """,
    output_key="final_plan",
    # before_agent_callback=opik_tracer.before_agent_callback,
    # after_agent_callback=opik_tracer.after_agent_callback,
    # before_model_callback=opik_tracer.before_model_callback,
    # after_model_callback=opik_tracer.after_model_callback
)

# Pipeline
planning_pipeline = SequentialAgent(
    name="WeeklyPlanningPipeline",
    sub_agents=[skeleton_agent, retrieval_agent, assembler_agent],
    description="Generates skeleton, retrieves workouts, and assembles plan."
)

# Track the pipeline
opik_tracer_pipeline = OpikTracer(
    name="fitness-planner-pipeline",
    tags=["planning", "rag", "multi-agent"],
    project_name="fitness_coach"
)
track_adk_agent_recursive(planning_pipeline, opik_tracer_pipeline)

# opik_tracer_skeleton_agent = OpikTracer(
#     name="skeleton-agent",
#     tags=["planning", "rag", "multi-agent"],
#     project_name="fitness_coach"
# )
# track_adk_agent_recursive(skeleton_agent, opik_tracer_skeleton_agent)

# opik_tracer_retrieval_agent = OpikTracer(
#     name="retrieval-agent",
#     tags=["planning", "rag", "multi-agent"],
#     project_name="fitness_coach"
# )
# track_adk_agent_recursive(retrieval_agent, opik_tracer_retrieval_agent)

# opik_tracer_assembler_agent = OpikTracer(
#     name="assembler-agent",
#     tags=["planning", "rag", "multi-agent"],
#     project_name="fitness_coach"
# )
# track_adk_agent_recursive(assembler_agent, opik_tracer_assembler_agent)



async def _run_agent_with_retry(runner, user_id, session_id, message, max_retries=3):
    """Runs an agent with exponential backoff for 429 errors."""
    delay = 5  # Start with 5s
    full_text = ""
    
    for attempt in range(max_retries + 1):
        try:
            full_text = "" # Reset for each attempt
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
                 if event.content and event.content.parts:
                     for part in event.content.parts:
                         if part.text: full_text += part.text
            return full_text
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries:
                    print(f"  [429 Error] Retrying in {delay}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(delay)
                    delay *= 2 # Exponential backoff
                else:
                    raise e
            else:
                raise e
    return full_text

async def generate_weekly_plan_rag(user_goal: str, available_workouts: list = None) -> dict:
    """
    Generates a 1-week workout plan using ADK Agents and Vector Search (Manual Orchestration).
    """
    session_service = InMemorySessionService()
    user_id = "user_" + str(uuid.uuid4())[:8]
    session_id = "session_" + str(uuid.uuid4())[:8]
    app_name = "fitness_coach_planner"
    
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )
    
    print(f"Generating plan for: {user_goal}")

    # 1. Run Skeleton Agent
    print("--- Step 1: Generating Skeleton ---")
    skeleton_runner = Runner(agent=skeleton_agent, app_name=app_name, session_service=session_service)
    prompt = f"Create a workout plan for goal: {user_goal}"
    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    
    skeleton_text = ""
    try:
        skeleton_text = await _run_agent_with_retry(skeleton_runner, user_id, session_id, content)
    except Exception as e:
        print(f"Skeleton Agent Error: {e}")
        return _fallback_error_plan(str(e))

    # Parse Skeleton
    try:
        clean_skel = skeleton_text.replace("```json", "").replace("```", "").strip()
        # Handle potential leading text before json
        if "{" in clean_skel:
            clean_skel = clean_skel[clean_skel.find("{"):clean_skel.rfind("}")+1]
        skeleton_json = json.loads(clean_skel)
        print("Skeleton generated successfully.")
    except Exception as e:
        print(f"Skeleton parsing failed: {e}\nText: {skeleton_text}")
        return _fallback_error_plan("Failed to parse skeleton")

    # 2. Manual Retrieval Loop
    print("--- Step 2: Retrieving Workouts ---")
    schedule = []
    days = skeleton_json.get("days", [])
    
    for day in days:
        day_num = day.get("day")
        query = day.get("search_query", "")
        focus = day.get("focus", "")
        
        selected_workout = None
        
        # Check if it's a rest day
        is_rest = False
        focus_lower = focus.lower()
        if "rest" in focus_lower or "recovery" in focus_lower or "stretch" in focus_lower:
             is_rest = True
             
        if not is_rest and query:
             try:
                 # Call tool directly
                 results_json = search_workouts_tool(query)
                 results = json.loads(results_json)
                 
                 if results and isinstance(results, list) and len(results) > 0:
                     # Pick the first one (best match)
                     first = results[0]
                     # Verify it's not an error/fallback
                     if not str(first.get("id", "")).startswith("fallback"):
                         selected_workout = first
                     else:
                         print(f"  Day {day_num}: Tool returned fallback for '{query}'")
                 else:
                     print(f"  Day {day_num}: No results for '{query}'")
             except Exception as e:
                 print(f"  Day {day_num}: Retrieval error: {e}")
        
        schedule.append({
            "day": day_num,
            "focus": focus,
            "selected_workout": selected_workout
        })
        
    retrieved_plan = {"schedule": schedule}
    
    # Update Session State for Assembler
    session = await session_service.get_session(app_name=app_name, session_id=session_id, user_id=user_id)
    # Store as string to simulate LLM context or object if supported
    # Storing as object in state is better if Agent can read it. 
    # But instructions say "check session state". 
    session.state["retrieved_plan"] = json.dumps(retrieved_plan) 
    
    # 3. Run Assembler Agent
    print("--- Step 3: Assembling Plan ---")
    assembler_runner = Runner(agent=assembler_agent, app_name=app_name, session_service=session_service)
    
    # Pass the plan explicitly in the prompt to avoid "code writing" behavior
    retrieved_plan_str = json.dumps(retrieved_plan, indent=2)
    assemble_prompt = f"""
    Assemble the final plan based on the following retrieved plan:
    
    {retrieved_plan_str}
    
    Output ONLY JSON.
    """
    assemble_content = types.Content(role="user", parts=[types.Part(text=assemble_prompt)])
    
    final_text = ""
    try:
        final_text = await _run_agent_with_retry(assembler_runner, user_id, session_id, assemble_content)
    except Exception as e:
        print(f"Assembler Agent Error: {e}")
        return _fallback_error_plan(str(e))
                 
    # Parse Final Plan
    final_plan_json = None
    try:
        clean_text = final_text.replace("```json", "").replace("```", "").strip()
        if "{" in clean_text:
            clean_text = clean_text[clean_text.find("{"):clean_text.rfind("}")+1]
        final_plan_json = json.loads(clean_text)
        print("Plan assembled successfully.")
    except Exception as e:
        print(f"Final plan parsing failed: {e}\nText: {final_text}")
        return _fallback_error_plan("Failed to parse final plan")

    # 4. Enrich Final Plan
    if final_plan_json:
        return enrich_plan_with_details(final_plan_json, retrieved_plan)
            
    return _fallback_error_plan("Unknown error")

def _fallback_error_plan(error_msg):
    return {
        "weekly_focus": f"Error Generating Plan: {error_msg}",
        "schedule": [{"day": i, "day_name": d, "is_rest": True, "workout_id": None, "activity": "Rest"} for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], 1)]
    }


def enrich_plan_with_details(final_plan_json, retrieved_plan_json):
    """
    Helper function to merge workout details from retrieved_plan into final_plan.
    Merges based on Day Number to be robust against ID hallucinations.
    """
    day_details_map = {}
    
    if retrieved_plan_json and "schedule" in retrieved_plan_json:
        for day_item in retrieved_plan_json["schedule"]:
            day_num = day_item.get("day")
            w = day_item.get("selected_workout")
            if day_num is not None and w:
                day_details_map[day_num] = w
                
    if final_plan_json and "schedule" in final_plan_json:
        for day in final_plan_json["schedule"]:
            day_num = day.get("day")
            
            if day_num in day_details_map:
                w = day_details_map[day_num]
                # Overwrite/Enrich with authoritative data from Retrieval
                day["workout_details"] = w
                day["workout_id"] = w.get("id")
                # Update display info to match the actual workout
                day["activity"] = w.get("display_title") or w.get("title") or day.get("activity")
                # Ensure is_rest matches reality of having a workout
                day["is_rest"] = False
            elif day.get("is_rest") is False and not day.get("workout_id"):
                 # Assembler thought it's a workout day but Retrieval found nothing?
                 # Mark as rest to avoid broken UI
                 day["is_rest"] = True
                 day["activity"] = "Rest (No workout found)"
                
    return final_plan_json
