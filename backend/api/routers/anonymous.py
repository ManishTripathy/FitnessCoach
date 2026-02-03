from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
from backend.services.firebase_service import save_anonymous_session, get_anonymous_session, delete_anonymous_session, get_bucket, get_db, download_file_as_bytes
from backend.services.ai_service import analyze_body_image, generate_future_physique
from backend.core.deps import verify_firebase_token

router = APIRouter(prefix="/anonymous", tags=["anonymous"])

class AnalyzeRequest(BaseModel):
    session_id: str

class GenerateRequest(BaseModel):
    session_id: str
    goal: str

class MigrateRequest(BaseModel):
    session_id: str

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
        analysis = analyze_body_image(image_bytes)
        
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
    session = get_anonymous_session(request.session_id)
    if not session or "storage_path" not in session:
        raise HTTPException(status_code=404, detail="Session or photo not found")
        
    try:
        # Download source image
        image_bytes = download_file_as_bytes(session["storage_path"])
        
        # Generate
        generated_bytes = generate_future_physique(image_bytes, request.goal)
        
        # Upload generated image
        bucket = get_bucket()
        filename = f"{uuid.uuid4()}.jpg"
        save_path = f"anonymous/{request.session_id}/generated/{request.goal}_{filename}"
        blob = bucket.blob(save_path)
        blob.upload_from_string(generated_bytes, content_type="image/jpeg")
        blob.make_public()
        
        # Save to session
        # We want to append to a list or update a dict of generated images
        current_generated = session.get("generated_images", [])
        # Check if goal already exists and update it, or append
        existing_idx = next((i for i, item in enumerate(current_generated) if item["goal"] == request.goal), -1)
        
        new_entry = {
            "goal": request.goal,
            "url": blob.public_url,
            "path": save_path
        }
        
        if existing_idx >= 0:
            current_generated[existing_idx] = new_entry
        else:
            current_generated.append(new_entry)
            
        save_anonymous_session(request.session_id, {"generated_images": current_generated})
        
        return {"url": blob.public_url, "path": save_path, "goal": request.goal}
        
    except Exception as e:
        print(f"Error in generate_anonymous_physique: {e}")
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
        
        # 2. Update user profile with latest scan if needed (optional but good for UX)
        # For now, just ensuring data is linked is enough per requirements.
        
        # Clean up anonymous session
        delete_anonymous_session(session_id)
        
        return {"status": "success", "message": "Data migrated successfully"}
    except Exception as e:
        print(f"Error in migrate_anonymous_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
