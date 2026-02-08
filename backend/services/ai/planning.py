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
    print(f"[Tool] Searching workouts for: '{query}'")
    
    db = get_db()
    if not db:
        return json.dumps({"error": "Database not connected"})
    
    text_to_embed = f"{query}"
    # Remove focus parameter logic
    
    query_embedding = generate_text_embedding(text_to_embed)
    
    if not query_embedding:
        return json.dumps({"error": "Failed to generate embedding"})
        
    try:
        collection = db.collection('workout_library')
        
        # Use vector search
        from google.cloud.firestore_v1.vector import Vector
        from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
        
        # We assume the 'embedding' field exists and is indexed
        vector_query = collection.find_nearest(
            vector_field="embedding",
            query_vector=Vector(query_embedding),
            distance_measure=DistanceMeasure.COSINE,
            limit=3  # Fetch top 3 to give the agent options
        )
        
        results = vector_query.get()
        
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

        return json.dumps(workouts)
        
    except Exception as e:
        print(f"[Tool] Vector search failed: {e}")
        return json.dumps({"error": str(e)})

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
    before_agent_callback=opik_tracer.before_agent_callback,
    after_agent_callback=opik_tracer.after_agent_callback,
    before_model_callback=opik_tracer.before_model_callback,
    after_model_callback=opik_tracer.after_model_callback
)

# 2. Retrieval Specialist
retrieval_agent = Agent(
    name="RetrievalSpecialist",
    model="gemini-2.0-flash",
    instruction="""
    You are a Workout Retrieval Specialist.
    You will receive a Weekly Skeleton (check session state 'skeleton').
    
    Your task:
    1. Parse the skeleton.
    2. For EACH day in the skeleton that is NOT a Rest day:
       - Formulate a detailed search query including activity and focus (e.g. "High intensity leg workout for mass").
       - Call the `search_workouts_tool` with this `query`.
       - From the results, Select the BEST single workout that fits the flow.
       - You MUST use the actual 'id' returned by the tool. DO NOT invent IDs.
    3. For Rest days, explicitly set activity to "Rest" or "Active Recovery".
    
    Output Format:
    Return a JSON object with the selected workouts:
    {
       "schedule": [
          {"day": 1, "focus": "...", "selected_workout": { ... workout details ... } or null},
          ...
       ]
    }
    """,
    tools=[search_workouts_tool],
    output_key="retrieved_plan",
    before_agent_callback=opik_tracer.before_agent_callback,
    after_agent_callback=opik_tracer.after_agent_callback,
    before_model_callback=opik_tracer.before_model_callback,
    after_model_callback=opik_tracer.after_model_callback,
    before_tool_callback=opik_tracer.before_tool_callback,
    after_tool_callback=opik_tracer.after_tool_callback
)

# 3. Plan Assembler
assembler_agent = Agent(
    name="PlanAssembler",
    model="gemini-2.0-flash",
    instruction="""
    You are the Final Plan Assembler.
    You receive a schedule with selected workouts (check session state 'retrieved_plan').
    
    Your task:
    1. Review the plan for coherence.
    2. Add a "notes" field to each day explaining WHY this workout fits the flow.
    3. Ensure the format matches the strict frontend requirement.
    
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
    before_agent_callback=opik_tracer.before_agent_callback,
    after_agent_callback=opik_tracer.after_agent_callback,
    before_model_callback=opik_tracer.before_model_callback,
    after_model_callback=opik_tracer.after_model_callback
)

# Pipeline
planning_pipeline = SequentialAgent(
    name="WeeklyPlanningPipeline",
    sub_agents=[skeleton_agent, retrieval_agent, assembler_agent],
    description="Generates skeleton, retrieves workouts, and assembles plan."
)

# Track the pipeline
track_adk_agent_recursive(planning_pipeline, opik_tracer)


async def generate_weekly_plan_rag(user_goal: str, available_workouts: list = None) -> dict:
    """
    Generates a 1-week workout plan using ADK Agents and Vector Search.
    
    Args:
        user_goal: The user's fitness goal.
        available_workouts: Ignored (retrieval is done via vector search).
    """
    
    runner = Runner(
        agent=planning_pipeline,
        app_name="fitness_coach_planner",
        session_service=InMemorySessionService()
    )
    
    user_id = "user_" + str(uuid.uuid4())[:8]
    session_id = "session_" + str(uuid.uuid4())[:8]
    
    # Create session
    await runner.session_service.create_session(
        app_name="fitness_coach_planner",
        user_id=user_id,
        session_id=session_id
    )
    
    prompt = f"Create a workout plan for goal: {user_goal}"
    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    
    final_text = ""
    
    try:
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            # We are interested in the final output from the Assembler
            # But the runner yields events for all agents.
            # We capture the content as it streams.
            # However, for SequentialAgent, we need to know WHICH agent produced the content.
            # The last agent (Assembler) produces the final JSON.
            
            if event.content and event.content.parts:
                # We can check event.author if available, or just accumulate.
                # In SequentialAgent, usually the final response to the user is the output of the sequence.
                # But intermediate agents might also output.
                # Opik tracing will show details. For the return value, we need the JSON.
                
                # Logic: The PlanAssembler is the last one.
                if hasattr(event, 'author') and event.author == "PlanAssembler":
                    for part in event.content.parts:
                        if part.text:
                            final_text += part.text
                elif not hasattr(event, 'author'):
                     # Fallback if author not set (sometimes happens in simple runners)
                     # But with SequentialAgent, it should be set.
                     # Let's accumulate everything and try to parse the last JSON block.
                     pass

    except Exception as e:
        print(f"ADK Pipeline Error: {e}")
        # Return fallback
        return {
            "weekly_focus": "Error Generating Plan",
            "schedule": [{"day": i, "day_name": d, "is_rest": True, "workout_id": None, "activity": "Rest", "notes": f"Error: {str(e)}"} for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], 1)]
        }
        
    # Parse the accumulated text
    # Since we might have missed 'author' check or it might stream in chunks, 
    # and we know the last agent outputs the JSON we want.
    # Let's actually assume the 'final_text' logic needs to be robust.
    
    # Better approach: Read from session state if possible? 
    # InMemoryRunner session state might hold the output_keys.
    
    session = await runner.session_service.get_session(app_name="fitness_coach_planner", session_id=session_id, user_id=user_id)
    
    final_plan_json = None
    retrieved_plan_json = None

    # 1. Parse Retrieved Plan (to get workout details)
    if session and session.state and "retrieved_plan" in session.state:
        try:
            r_plan_content = session.state["retrieved_plan"]
            if hasattr(r_plan_content, 'parts'):
                r_text = extract_text_from_content(r_plan_content)
            else:
                r_text = str(r_plan_content)
            
            r_clean = r_text.replace("```json", "").replace("```", "").strip()
            retrieved_plan_json = json.loads(r_clean)
        except Exception as e:
            print(f"Error parsing retrieved_plan for details: {e}")

    # 2. Parse Final Plan
    if session and session.state and "final_plan" in session.state:
        try:
            plan_text = session.state["final_plan"]
            if hasattr(plan_text, 'parts'): # Content object
                text = extract_text_from_content(plan_text)
            else:
                text = str(plan_text)
                
            clean_text = text.replace("```json", "").replace("```", "").strip()
            final_plan_json = json.loads(clean_text)
        except Exception as e:
            print(f"Error parsing session state final_plan: {e}")
    
    # Fallback if final_plan not in session (captured from stream)
    if not final_plan_json and final_text:
        try:
            clean_text = final_text.replace("```json", "").replace("```", "").strip()
            final_plan_json = json.loads(clean_text)
        except Exception as e:
            print(f"Error parsing captured text: {e}")

    # 3. Enrich Final Plan with Details
    if final_plan_json:
        return enrich_plan_with_details(final_plan_json, retrieved_plan_json)
            
    # Ultimate Fallback
    return {
        "weekly_focus": "Fallback Plan (Parsing Error)",
        "schedule": [{"day": i, "day_name": d, "is_rest": True, "workout_id": None, "activity": "Rest"} for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], 1)]
    }

def enrich_plan_with_details(final_plan_json, retrieved_plan_json):
    """
    Helper function to merge workout details from retrieved_plan into final_plan.
    """
    workout_details_map = {}
    
    if retrieved_plan_json and "schedule" in retrieved_plan_json:
        for day_item in retrieved_plan_json["schedule"]:
            w = day_item.get("selected_workout")
            if w and isinstance(w, dict) and w.get("id"):
                workout_details_map[w["id"]] = w
                
    if final_plan_json and "schedule" in final_plan_json:
        for day in final_plan_json["schedule"]:
            w_id = day.get("workout_id")
            if w_id and w_id in workout_details_map:
                day["workout_details"] = workout_details_map[w_id]
            elif w_id:
                print(f"Warning: Details missing for workout_id {w_id}")
                
    return final_plan_json
