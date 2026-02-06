from fastapi import APIRouter, Depends, HTTPException, Body
from backend.core.deps import verify_firebase_token
from backend.services.firebase_service import get_db, download_file_as_bytes
from backend.services.ai_service import recommend_fitness_path
from backend.services.mock_service import try_get_mock_suggest
from pydantic import BaseModel
from typing import List, Dict, Optional
import datetime
import asyncio

router = APIRouter(prefix="/decide", tags=["decide"])

class GeneratedImage(BaseModel):
    url: str
    path: str
    goal: str

class AnalysisData(BaseModel):
    category: str
    reasoning: str

class SaveStateRequest(BaseModel):
    original_image_path: str
    analysis: AnalysisData
    generated_images: List[GeneratedImage]

class CommitPathRequest(BaseModel):
    selected_path: str  # lean | athletic | muscle
    source: str         # user_selected | ai_suggested
    ai_recommendation: Optional[Dict] = None

@router.post("/save")
async def save_state(
    request: SaveStateRequest,
    token: dict = Depends(verify_firebase_token)
):
    try:
        user_id = token['uid']
        db = get_db()
        
        # Construct data to save
        data = {
            "userId": user_id,
            "originalImage": request.original_image_path,
            "analysis": request.analysis.dict(),
            "generatedImages": [img.dict() for img in request.generated_images],
            "observeCompleted": True,
            "decideCompleted": False, # Initially false until path is committed
            "lastUpdated": datetime.datetime.utcnow()
        }
        
        db.collection("user_progress").document(user_id).set(data, merge=True)
        
        return {"status": "success", "message": "Progress saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/state")
async def get_state(token: dict = Depends(verify_firebase_token)):
    try:
        user_id = token['uid']
        db = get_db()
        
        doc = db.collection("user_progress").document(user_id).get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            return {"observeCompleted": False, "decideCompleted": False}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest")
async def suggest_path(token: dict = Depends(verify_firebase_token)):
    mock_res = try_get_mock_suggest("User")
    if mock_res:
        return mock_res

    try:
        user_id = token['uid']
        db = get_db()
        
        # 1. Fetch current state to get image paths
        doc = db.collection("user_progress").document(user_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="No progress found. Please complete the Observe phase first.")
        
        data = doc.to_dict()
        original_path = data.get("originalImage")
        generated_images = data.get("generatedImages", [])
        
        if not original_path or len(generated_images) < 3:
             raise HTTPException(status_code=400, detail="Missing images for analysis.")

        # Map goals to paths
        image_paths = {img['goal']: img['path'] for img in generated_images}
        
        if not all(k in image_paths for k in ['lean', 'athletic', 'muscle']):
             raise HTTPException(status_code=400, detail="Missing one or more goal images.")

        # 2. Download images (Parallel)
        # We need bytes for the AI
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(None, download_file_as_bytes, original_path),
            loop.run_in_executor(None, download_file_as_bytes, image_paths['lean']),
            loop.run_in_executor(None, download_file_as_bytes, image_paths['athletic']),
            loop.run_in_executor(None, download_file_as_bytes, image_paths['muscle'])
        ]
        
        results = await asyncio.gather(*tasks)
        original_bytes, lean_bytes, athletic_bytes, muscle_bytes = results
        
        # 3. Call AI Service
        # recommend_fitness_path is now async
        recommendation = await recommend_fitness_path(
            original_bytes, lean_bytes, athletic_bytes, muscle_bytes
        )
        
        return recommendation
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/commit")
async def commit_path(
    request: CommitPathRequest,
    token: dict = Depends(verify_firebase_token)
):
    try:
        user_id = token['uid']
        db = get_db()
        
        # Update user progress
        data = {
            "selectedPath": request.selected_path,
            "decisionSource": request.source,
            "aiRecommendation": request.ai_recommendation,
            "decideCompleted": True,
            "decisionTimestamp": datetime.datetime.utcnow(),
            "lastUpdated": datetime.datetime.utcnow()
        }
        
        db.collection("user_progress").document(user_id).set(data, merge=True)
        
        return {"status": "success", "message": "Path committed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
