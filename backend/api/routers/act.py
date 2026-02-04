from fastapi import APIRouter, HTTPException, Depends
from backend.core.deps import verify_firebase_token
from backend.services.ai_service import generate_weekly_plan_rag
from backend.services.firebase_service import get_db
from backend.services.mock_service import try_get_mock_plan
from backend.core.config import settings
from pydantic import BaseModel
from typing import List, Optional
import datetime
import os
import json

router = APIRouter(prefix="/act", tags=["act"])

class GeneratePlanRequest(BaseModel):
    force_refresh: bool = False

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
        
        if user_doc.exists:
            data = user_doc.to_dict()
            existing_plan = data.get("weeklyPlan")
            if existing_plan and not request.force_refresh:
                return {"status": "exists", "plan": existing_plan}
            
            # Get User Goal (selected path)
            user_goal = data.get("selectedPath", "lean") # Default to lean
        else:
            raise HTTPException(status_code=404, detail="User progress not found")

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
        ai_result = generate_weekly_plan_rag(user_goal, workout_library)
        
        # 4. Enrich plan with full workout details (thumbnails, urls)
        enriched_schedule = []
        for day in ai_result.get("schedule", []):
            if not day.get("is_rest") and day.get("workout_id"):
                w_id = day["workout_id"]
                if w_id in workout_map:
                    day["workout_details"] = workout_map[w_id]
            enriched_schedule.append(day)
            
        ai_result["schedule"] = enriched_schedule
        ai_result["generated_at"] = datetime.datetime.utcnow().isoformat()
        
        # 5. Save to Firestore
        user_ref.set({
            "weeklyPlan": ai_result,
            "actPhaseStarted": True,
            "lastUpdated": datetime.datetime.utcnow()
        }, merge=True)
        
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
