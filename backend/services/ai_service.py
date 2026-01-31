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
        # We'll iterate to get just one model to verify access
        models_iter = client.models.list()
        first_model = next(models_iter, None)
        
        status["initialized"] = True
        status["connectivity"] = "connected"
        status["details"] = f"Successfully connected. Found model: {first_model.name if first_model else 'None'}"
        
    except Exception as e:
        status["connectivity"] = "failed"
        status["error"] = str(e)
        
    return status
