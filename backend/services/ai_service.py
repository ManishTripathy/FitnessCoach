from google import genai
from backend.core.config import settings

def check_ai_connection():
    status = {
        "initialized": False,
        "api_key_present": False,
        "connectivity": "unknown",
        "error": None
    }
    
    if not settings.GOOGLE_API_KEY:
        status["error"] = "GOOGLE_API_KEY not found in environment variables"
        return status
        
    status["api_key_present"] = True
    
    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        # Simple test to list models or generate a tiny content
        # Listing models is a good connectivity check
        # We'll try to list one model
        models = list(client.models.list(config={"limit": 1}))
        
        status["initialized"] = True
        status["connectivity"] = "connected"
        status["details"] = f"Successfully listed {len(models)} models"
        
    except Exception as e:
        status["connectivity"] = "failed"
        status["error"] = str(e)
        
    return status
