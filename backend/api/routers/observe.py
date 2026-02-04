from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import uuid

from backend.core.deps import verify_firebase_token
from backend.services.firebase_service import download_file_as_bytes, get_bucket, get_db
from backend.services.ai_service import analyze_body_image, generate_future_physique
from backend.services.mock_service import try_get_mock_analyze, try_get_mock_generate

router = APIRouter(prefix="/observe", tags=["observe"])

class AnalyzeRequest(BaseModel):
    storage_path: str

class GenerateRequest(BaseModel):
    storage_path: str
    goal: str # lean, athletic, muscle

@router.post("/analyze")
async def analyze_body(request: AnalyzeRequest, token=Depends(verify_firebase_token)):
    mock_res = try_get_mock_analyze("User")
    if mock_res:
        return mock_res

    try:
        # 1. Download image
        image_bytes = download_file_as_bytes(request.storage_path)
        
        # 2. Analyze
        analysis = analyze_body_image(image_bytes)
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str, token=Depends(verify_firebase_token)):
    user_id = token['uid']
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    doc_ref = db.collection('users').document(user_id).collection('scans').document(scan_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Scan not found")
        
    return doc.to_dict()

@router.post("/generate")
async def generate_physique(request: GenerateRequest, token=Depends(verify_firebase_token)):
    mock_res = try_get_mock_generate("User")
    if mock_res:
        # Override mock goal with requested goal
        mock_res_copy = mock_res.copy()
        mock_res_copy["goal"] = request.goal
        return mock_res_copy

    try:
        print(f"Generating physique for goal: {request.goal}")
        # 1. Download source image
        image_bytes = download_file_as_bytes(request.storage_path)
        print("Image downloaded successfully")
        
        # 2. Generate
        generated_bytes = generate_future_physique(image_bytes, request.goal)
        print("Image generated successfully")
        
        # 3. Upload generated image
        bucket = get_bucket()
        user_id = token['uid']
        filename = f"{uuid.uuid4()}.jpg"
        save_path = f"users/{user_id}/observe/generated/{request.goal}_{filename}"
        blob = bucket.blob(save_path)
        blob.upload_from_string(generated_bytes, content_type="image/jpeg")
        blob.make_public() # Or use signed URL
        
        return {"url": blob.public_url, "path": save_path}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in generate_physique: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except BaseException as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR in generate_physique: {e}")
        # Prevent server shutdown if possible by raising standard HTTP exception
        raise HTTPException(status_code=500, detail="Critical Server Error")
