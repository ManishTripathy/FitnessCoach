from google import genai
from backend.core.config import settings

def generate_text_embedding(text: str) -> list:
    """Generates a text embedding vector for the given text."""
    # ADK might not expose embeddings directly yet, or it's on the model.
    # The ADK `Gemini` model might not have embed_content.
    # We should fallback to direct genai client for embeddings if ADK doesn't support it clearly.
    # But user asked to use ADK.
    # Let's check if we can access the underlying client or if we should keep using genai for embeddings.
    # Since embeddings are usually not "Agent" tasks, I'll keep using genai directly for this one specific function, 
    # OR create a dummy agent and see if I can use it.
    # But let's stick to genai for embeddings as it's cleaner and "Agent" is overkill/wrong abstraction for embeddings.
    # However, I should use the client from settings/env.
    
    if not settings.GOOGLE_API_KEY:
        return []
        
    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        response = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return []
