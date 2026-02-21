import json
import os
import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
from firebase_admin import firestore
from backend.services.firebase_service import save_anonymous_session, get_anonymous_session, delete_anonymous_session, get_bucket, get_db, download_file_as_bytes
from backend.services.ai_service import analyze_body_image, generate_future_physique, recommend_fitness_path, generate_weekly_plan_rag
from backend.services.ai.agent import detect_intent_multi_agent, adjust_workout_multi_agent
from backend.services.mock_service import try_get_mock_plan, try_get_mock_analyze, try_get_mock_generate, try_get_mock_suggest
from backend.core.deps import verify_firebase_token
from backend.core.config import settings

router = APIRouter(prefix="/anonymous", tags=["anonymous"])

class AnalyzeRequest(BaseModel):
    session_id: str

class GenerateRequest(BaseModel):
    session_id: str
    goal: str

class PlanRequest(BaseModel):
    goal: str

class MigrateRequest(BaseModel):
    session_id: str

class AnonymousChatRequest(BaseModel):
    message: str
    day_id: str
    current_plan: dict
    confirm: bool = False

@router.post("/upload")
async def upload_anonymous_photo(file: UploadFile = File(...), session_id: str = Form(None)):
    if not session_id or session_id == "null" or session_id == "":
        session_id = str(uuid.uuid4())
    
    try:
        # Upload to Firebase Storage
        bucket = get_bucket()
        blob_path = f"anonymous/{session_id}/{file.filename}"
        blob = bucket.blob(blob_path)
        blob.upload_from_file(file.file, content_type=file.content_type)
        blob.make_public()
        
        # Save session data
        session_data = {
            "session_id": session_id,
            "uploaded_photo_url": blob.public_url,
            "storage_path": blob_path,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        save_anonymous_session(session_id, session_data)
        
        return {"session_id": session_id, "url": blob.public_url, "storage_path": blob_path}
    except Exception as e:
        print(f"Error in upload_anonymous_photo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_anonymous(request: AnalyzeRequest):
    mock_res = try_get_mock_analyze("Anonymous")
    if mock_res:
        save_anonymous_session(request.session_id, {"analysis_results": mock_res})
        return mock_res

    session = get_anonymous_session(request.session_id)
    if not session or "storage_path" not in session:
        raise HTTPException(status_code=404, detail="Session or photo not found")
    
    # Check expiration
    if "expires_at" in session:
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.utcnow() > expires_at:
            # Optionally delete the expired session here or let a background job do it
            delete_anonymous_session(request.session_id)
            raise HTTPException(status_code=404, detail="Session expired")

    # Download and Analyze
    try:
        image_bytes = download_file_as_bytes(session["storage_path"])
        analysis = await analyze_body_image(image_bytes)
        
        # Save results
        save_anonymous_session(request.session_id, {"analysis_results": analysis})
        return analysis
    except Exception as e:
        print(f"Error in analyze_anonymous: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{session_id}")
async def get_anonymous_results(session_id: str):
    session = get_anonymous_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/generate")
async def generate_anonymous_physique(request: GenerateRequest):
    mock_res = try_get_mock_generate("Anonymous")
    if mock_res:
        # We need to simulate the saving logic too
        session = get_anonymous_session(request.session_id)
        if not session:
             raise HTTPException(status_code=404, detail="Session not found")
             
        current_generated = session.get("generated_images", [])
        existing_idx = next((i for i, item in enumerate(current_generated) if item["goal"] == request.goal), -1)
        
        # Override mock goal with requested goal
        new_entry = mock_res.copy()
        new_entry["goal"] = request.goal
        
        if existing_idx >= 0:
            current_generated[existing_idx] = new_entry
        else:
            current_generated.append(new_entry)
            
        save_anonymous_session(request.session_id, {"generated_images": current_generated})
        return new_entry

    session = get_anonymous_session(request.session_id)
    if not session or "storage_path" not in session:
        raise HTTPException(status_code=404, detail="Session or photo not found")
        
    try:
        # Download source image
        image_bytes = download_file_as_bytes(session["storage_path"])
        
        # Generate
        generated_bytes = await generate_future_physique(image_bytes, request.goal)
        
        # Upload generated image
        bucket = get_bucket()
        filename = f"{uuid.uuid4()}.jpg"
        save_path = f"anonymous/{request.session_id}/generated/{request.goal}_{filename}"
        blob = bucket.blob(save_path)
        blob.upload_from_string(generated_bytes, content_type="image/jpeg")
        blob.make_public()
        
        # Save to session safely using transaction to avoid race conditions
        new_entry = {
            "goal": request.goal,
            "url": blob.public_url,
            "path": save_path
        }

        @firestore.transactional
        def update_session_transaction(transaction, session_ref, entry):
            snapshot = session_ref.get(transaction=transaction)
            if not snapshot.exists:
                return False
            
            session_data = snapshot.to_dict()
            current_generated = session_data.get("generated_images", [])
            
            # Check if goal already exists and update it, or append
            existing_idx = next((i for i, item in enumerate(current_generated) if item["goal"] == entry["goal"]), -1)
            
            if existing_idx >= 0:
                current_generated[existing_idx] = entry
            else:
                current_generated.append(entry)
                
            transaction.update(session_ref, {"generated_images": current_generated})
            return True

        db = get_db()
        session_ref = db.collection('anonymous_sessions').document(request.session_id)
        transaction = db.transaction()
        update_session_transaction(transaction, session_ref, new_entry)
        
        return {"url": blob.public_url, "path": save_path, "goal": request.goal}
        
    except Exception as e:
        print(f"Error in generate_anonymous_physique: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest")
async def suggest_anonymous_path(request: AnalyzeRequest):
    mock_res = try_get_mock_suggest("Anonymous")
    if mock_res:
        return mock_res

    session = get_anonymous_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if "storage_path" not in session:
        raise HTTPException(status_code=400, detail="Original image not found in session.")
        
    original_path = session["storage_path"]
    generated_images = session.get("generated_images", [])
    
    if len(generated_images) < 3:
         raise HTTPException(status_code=400, detail="Missing generated images. Please wait for all transformations.")

    # Map goals to paths
    image_paths = {img['goal']: img['path'] for img in generated_images}
    
    if not all(k in image_paths for k in ['lean', 'athletic', 'muscle']):
         raise HTTPException(status_code=400, detail="Missing one or more goal images.")

    try:
        import asyncio
        # Download images (Parallel)
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(None, download_file_as_bytes, original_path),
            loop.run_in_executor(None, download_file_as_bytes, image_paths['lean']),
            loop.run_in_executor(None, download_file_as_bytes, image_paths['athletic']),
            loop.run_in_executor(None, download_file_as_bytes, image_paths['muscle'])
        ]
        
        results = await asyncio.gather(*tasks)
        original_bytes, lean_bytes, athletic_bytes, muscle_bytes = results
        
        # Call AI Service
        # Now recommend_fitness_path is async, so we await it directly
        recommendation = await recommend_fitness_path(
            original_bytes, lean_bytes, athletic_bytes, muscle_bytes
        )
        
        return recommendation
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan")
async def generate_anonymous_plan(request: PlanRequest):
    mock_plan = try_get_mock_plan("Anonymous")
    if mock_plan:
        return mock_plan

    print(f"[{datetime.utcnow().isoformat()}] MODE: AI - Generating Anonymous Plan")
    try:
        db = get_db()
        
        # 1. Fetch Workouts from Library
        workouts_ref = db.collection("workout_library").stream()
        workout_library = []
        workout_map = {} 
        
        for doc in workouts_ref:
            w_data = doc.to_dict()
            w_data['id'] = doc.id
            if 'embedding' in w_data:
                del w_data['embedding']
            workout_library.append(w_data)
            workout_map[doc.id] = w_data

        if not workout_library:
            raise HTTPException(status_code=500, detail="Workout library is empty.")

        # 2. Generate Plan via AI
        ai_result = await generate_weekly_plan_rag(request.goal, workout_library)
        
        # 3. Enrich plan
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
        ai_result["generated_at"] = datetime.utcnow().isoformat()
        
        return ai_result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def anonymous_chat_agent(request: AnonymousChatRequest):
    try:
        day_match = re.search(r'day-(\d+)', request.day_id)
        if not day_match:
            raise HTTPException(status_code=400, detail="Invalid day_id format")
        day_index = int(day_match.group(1))

        current_plan = request.current_plan or {}
        schedule = current_plan.get("schedule") or []
        if not schedule:
            raise HTTPException(status_code=400, detail="current_plan.schedule is required")

        target_day = next((d for d in schedule if d.get("day") == day_index), None)
        workout_details = target_day.get("workout_details") if target_day else {}
        context = {
            "day_index": day_index,
            "workout_title": target_day.get("activity") if target_day else "Unknown",
            "current_duration_mins": (workout_details or {}).get("duration_mins"),
            "current_focus": (workout_details or {}).get("focus"),
        }

        intent_data = await detect_intent_multi_agent(request.message, context)
        intent = str(intent_data.get("intent", "OTHER")).upper()

        if intent == "ADJUST_WORKOUT":
            adjustment_result = await adjust_workout_multi_agent(
                request.message,
                day_index,
                current_plan,
                intent_data,
            )

            if adjustment_result.get("success"):
                new_schedule = []
                updated_day_data = None

                for day in current_plan.get("schedule", []):
                    if day.get("day") == day_index:
                        day["is_rest"] = adjustment_result["is_rest"]
                        day["workout_id"] = adjustment_result["new_workout_id"]
                        selected_workout = adjustment_result.get("selected_workout") or {}
                        day["activity"] = (
                            adjustment_result.get("new_activity_title")
                            or selected_workout.get("display_title")
                            or selected_workout.get("title")
                            or day.get("activity")
                        )
                        day["notes"] = adjustment_result["summary"]

                        if not day["is_rest"] and day["workout_id"]:
                            day["workout_details"] = selected_workout
                        else:
                            day["workout_details"] = None
                            if not day.get("activity"):
                                day["activity"] = "Rest"

                        updated_day_data = day
                    new_schedule.append(day)

                current_plan["schedule"] = new_schedule

                if request.confirm:
                    return {
                        "status": "success",
                        "action": "ADJUST_WORKOUT",
                        "response_text": adjustment_result["agent_response"],
                        "summary": adjustment_result["summary"],
                        "updated_day": updated_day_data,
                        "updated_plan": current_plan,
                    }
                else:
                    proposed_title = (
                        adjustment_result.get("new_activity_title")
                        or selected_workout.get("display_title")
                        or selected_workout.get("title")
                        or target_day.get("activity")
                        or "this workout"
                    )
                    proposed_duration = selected_workout.get("duration_mins")
                    is_rest = adjustment_result.get("is_rest", False)
                    if is_rest:
                        response_text = (
                            f"I couldn't find a workout that fits your request well for Day {day_index}. "
                            f"One option is to make it a rest day so your body can recover. "
                            f"Are you okay if I change Day {day_index} to a rest day?"
                        )
                    else:
                        if isinstance(proposed_duration, (int, float)):
                            response_text = (
                                f"Got it. Based on what you said, I would switch Day {day_index} to "
                                f"\"{proposed_title}\" which is about {int(proposed_duration)} minutes "
                                f"and matches your focus. Are you okay if I update Day {day_index} to this?"
                            )
                        else:
                            response_text = (
                                f"Got it. I have a workout called \"{proposed_title}\" that I think fits "
                                f"what you asked for on Day {day_index}. Are you okay if I update "
                                f"Day {day_index} to this?"
                            )
                    return {
                        "status": "proposal",
                        "action": "ADJUST_WORKOUT",
                        "response_text": response_text,
                        "summary": adjustment_result["summary"],
                        "updated_day": updated_day_data,
                        "updated_plan": current_plan,
                        "confirm_required": True,
                    }
            else:
                return {
                    "status": "error",
                    "response_text": adjustment_result.get("agent_response", "Failed to adjust."),
                }

        return {
            "status": "success",
            "action": "chat",
            "response_text": "I can currently help with adjusting your workout plan (for example, 'make it shorter' or 'too hard').",
            "summary": None,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Anonymous chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migrate")
async def migrate_anonymous_data(request: MigrateRequest, token=Depends(verify_firebase_token)):
    session_id = request.session_id
    user_id = token['uid']
    
    session = get_anonymous_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Anonymous session not found")
        
    try:
        db = get_db()
        # Save to user's history/profile. 
        # We can also update the 'users/{user_id}' doc directly if it's the "current" state
        # But let's add it to a 'scans' subcollection for now to allow history.
        
        # Also, we might want to update the main profile "current_physique" if it's empty.
        
        # 1. Add to scans history
        scan_ref = db.collection('users').document(user_id).collection('scans').document(session_id)
        # Add user_id to the data
        session['user_id'] = user_id
        session['migrated_at'] = datetime.utcnow().isoformat()
        scan_ref.set(session)
        
        # 2. Update user_progress for the Decide phase
        # Map anonymous session structure to user_progress structure
        progress_data = {
            "userId": user_id,
            "originalImage": session.get("storage_path"),
            "analysis": session.get("analysis_results", {}),
            "generatedImages": session.get("generated_images", []),
            "observeCompleted": True,
            "decideCompleted": False,
            "lastUpdated": datetime.utcnow()
        }
        db.collection("user_progress").document(user_id).set(progress_data, merge=True)
        
        # Clean up anonymous session
        delete_anonymous_session(session_id)
        
        return {"status": "success", "message": "Data migrated successfully"}
    except Exception as e:
        print(f"Error in migrate_anonymous_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
