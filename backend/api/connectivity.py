from fastapi import APIRouter
from backend.services.firebase_service import check_firebase_connection
from backend.services.ai_service import check_ai_connection

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Fitness Coach Backend Running"}

@router.get("/connectivity/firebase")
async def firebase_connectivity():
    return check_firebase_connection()

@router.get("/connectivity/ai")
async def ai_connectivity():
    return await check_ai_connection()

@router.get("/connectivity/all")
async def all_connectivity():
    return {
        "firebase": check_firebase_connection(),
        "ai": await check_ai_connection()
    }
