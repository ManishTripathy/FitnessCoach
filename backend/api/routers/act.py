from fastapi import APIRouter, HTTPException, Depends
from backend.core.deps import verify_firebase_token
from backend.services.ai_service import generate_weekly_plan_rag
from backend.services.ai.agent import detect_intent_multi_agent, adjust_workout_multi_agent
from backend.services.firebase_service import get_db
from backend.services.mock_service import try_get_mock_plan
from backend.core.config import settings
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime
import os
import json
import re

router = APIRouter(prefix="/act", tags=["act"])

class GeneratePlanRequest(BaseModel):
    force_refresh: bool = False
    goal: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    day_id: str
    current_plan: Optional[Dict[str, Any]] = None

@router.post("/chat")
async def chat_agent(
    request: ChatRequest,
    token: dict = Depends(verify_firebase_token)
):
    try:
        user_id = token['uid']
        db = get_db()
        
        # Parse day index (e.g. "day-1" -> 1)
        day_match = re.search(r'day-(\d+)', request.day_id)
        if not day_match:
            raise HTTPException(status_code=400, detail="Invalid day_id format")
        day_index = int(day_match.group(1))
        
        # 1. Get Current Plan
        current_plan = request.current_plan
        if not current_plan:
            user_ref = db.collection("user_progress").document(user_id)
            user_doc = user_ref.get()
            if user_doc.exists:
                current_plan = user_doc.to_dict().get("weeklyPlan")
        
        if not current_plan:
            raise HTTPException(status_code=404, detail="No active plan found")

        # 2. Get Context (Workout for that day)
        target_day = next((d for d in current_plan.get('schedule', []) if d['day'] == day_index), None)
        workout_details = target_day.get("workout_details") if target_day else {}
        context = {
            "day_index": day_index,
            "workout_title": target_day.get('activity') if target_day else "Unknown",
            "current_duration_mins": workout_details.get("duration_mins") if workout_details else None,
            "current_focus": workout_details.get("focus") if workout_details else None
        }
        
        # 3. Detect Intent
        intent_data = await detect_intent_multi_agent(request.message, context)
        print("Intent Data:", intent_data)
        intent = str(intent_data.get("intent", "OTHER")).upper()
        print("Detected Intent:", intent)
        
        if intent == "ADJUST_WORKOUT":
            adjustment_result = await adjust_workout_multi_agent(
                request.message,
                day_index,
                current_plan,
                intent_data
            )
            
            if adjustment_result.get("success"):
                # Apply changes to the plan structure
                new_schedule = []
                updated_day_data = None
                
                for day in current_plan.get("schedule", []):
                    if day['day'] == day_index:
                        day['is_rest'] = adjustment_result['is_rest']
                        day['workout_id'] = adjustment_result['new_workout_id']
                        selected_workout = adjustment_result.get("selected_workout")
                        day['activity'] = adjustment_result.get('new_activity_title') or (selected_workout or {}).get("display_title") or (selected_workout or {}).get("title")
                        day['notes'] = adjustment_result['summary']
                        
                        if not day['is_rest'] and day['workout_id']:
                             day['workout_details'] = selected_workout
                        else:
                             day['workout_details'] = None
                             if not day.get('activity'):
                                  day['activity'] = "Rest"
                             
                        updated_day_data = day
                    new_schedule.append(day)
                
                current_plan["schedule"] = new_schedule
                
                # Save updated plan
                user_ref = db.collection("user_progress").document(user_id)
                user_ref.set({
                    "weeklyPlan": current_plan,
                    "lastUpdated": datetime.datetime.utcnow()
                }, merge=True)
                
                return {
                    "status": "success",
                    "action": "ADJUST_WORKOUT",
                    "response_text": adjustment_result['agent_response'],
                    "summary": adjustment_result['summary'],
                    "updated_day": updated_day_data,
                    "updated_plan": current_plan
                }
            else:
                 return {
                    "status": "error",
                    "response_text": adjustment_result.get("agent_response", "Failed to adjust.")
                }
        
        else:
            # Placeholder for other intents
            return {
                "status": "success",
                "action": "chat",
                "response_text": "I can currently only help with adjusting your workout plan (e.g., 'make it shorter', 'too hard'). Other features coming soon!",
                "summary": None
            }
            
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-plan")
async def generate_plan(
    request: GeneratePlanRequest,
    token: dict = Depends(verify_firebase_token)
):
    try:
        user_id = token['uid']
        db = get_db()
        
        # Mock Response if enabled
        mock_plan = try_get_mock_plan("User")
        if mock_plan:
            # Update generated_at for realism
            mock_plan["generated_at"] = datetime.datetime.utcnow().isoformat()
            
            # Save to Firestore (to mimic real behavior)
            user_ref = db.collection("user_progress").document(user_id)
            user_ref.set({
                "weeklyPlan": mock_plan,
                "actPhaseStarted": True,
                "lastUpdated": datetime.datetime.utcnow()
            }, merge=True)
            
            return {"status": "success", "plan": mock_plan}

        print(f"[{datetime.datetime.utcnow().isoformat()}] MODE: AI - Generating User Plan")
        # 1. Check if plan already exists and not forcing refresh
        user_ref = db.collection("user_progress").document(user_id)
        user_doc = user_ref.get()
        
        target_goal = request.goal
        if not target_goal:
            # Fallback to stored selectedPath if not provided
            if user_doc.exists:
                target_goal = user_doc.to_dict().get("selectedPath", "lean")
            else:
                target_goal = "lean"

        if user_doc.exists:
            data = user_doc.to_dict()
            
            # Check for multi-plan storage first
            weekly_plans = data.get("weeklyPlans", {})
            existing_plan = weekly_plans.get(target_goal)
            
            # Legacy fallback: check single weeklyPlan if it matches the goal (or we just assume it might be valid if we don't have multiple)
            # But to be safe and support the new feature, we prefer weeklyPlans.
            # If we don't have it in weeklyPlans, we check if the old single weeklyPlan exists and maybe migration is needed? 
            # For now, let's just generate new if not found in weeklyPlans to ensure correct goal.
            
            if existing_plan and not request.force_refresh:
                # Update current active weeklyPlan to this one
                user_ref.update({
                    "weeklyPlan": existing_plan,
                    "selectedPath": target_goal # Ensure selectedPath is in sync
                })
                return {"status": "exists", "plan": existing_plan}
            
            # If we are forcing refresh, or plan doesn't exist for this goal
            pass
        else:
            # New user doc will be created below
            pass

        # 2. Fetch Workouts from Library
        # In a real app with many workouts, we would use vector search here.
        # Since we have < 20, we fetch all.
        workouts_ref = db.collection("workout_library").stream()
        workout_library = []
        workout_map = {} # For quick lookup later
        
        for doc in workouts_ref:
            w_data = doc.to_dict()
            w_data['id'] = doc.id
            # Remove embedding to save bandwidth/tokens
            if 'embedding' in w_data:
                del w_data['embedding']
            workout_library.append(w_data)
            workout_map[doc.id] = w_data

        if not workout_library:
            raise HTTPException(status_code=500, detail="Workout library is empty. Please seed data.")

        # 3. Generate Plan via AI
        ai_result = await generate_weekly_plan_rag(target_goal, workout_library)
        
        # 4. Enrich plan with full workout details (thumbnails, urls)
        enriched_schedule = []
        for day in ai_result.get("schedule", []):
            if not day.get("is_rest") and day.get("workout_id"):
                w_id = day["workout_id"]
                if w_id in workout_map:
                    details = workout_map[w_id]
                    day["workout_details"] = details
                    day["activity"] = details["display_title"]
            enriched_schedule.append(day)
            
        ai_result["schedule"] = enriched_schedule
        ai_result["generated_at"] = datetime.datetime.utcnow().isoformat()
        
        # 5. Save to Firestore
        # We save it to weeklyPlans map AND the current weeklyPlan
        update_data = {
            "weeklyPlans": {
                target_goal: ai_result
            },
            "weeklyPlan": ai_result,
            "selectedPath": target_goal,
            "actPhaseStarted": True,
            "lastUpdated": datetime.datetime.utcnow()
        }
        
        user_ref.set(update_data, merge=True)
        
        return {"status": "success", "plan": ai_result}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plan")
async def get_plan(token: dict = Depends(verify_firebase_token)):
    try:
        user_id = token['uid']
        db = get_db()
        doc = db.collection("user_progress").document(user_id).get()
        
        if not doc.exists:
            return {"plan": None}
            
        data = doc.to_dict()
        return {"plan": data.get("weeklyPlan")}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
