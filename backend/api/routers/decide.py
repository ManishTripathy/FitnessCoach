from fastapi import APIRouter, Depends, HTTPException, Body
from backend.core.deps import verify_firebase_token
from backend.services.firebase_service import get_db
from pydantic import BaseModel
from typing import List, Dict, Optional
import datetime

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
            "decideCompleted": True,
            "lastUpdated": datetime.datetime.utcnow()
        }
        
        # Save to 'user_progress' collection (or 'users' subcollection)
        # Using a top-level 'user_progress' collection keyed by userId for simplicity
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
