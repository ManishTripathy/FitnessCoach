from google import genai
from backend.core.config import settings
import os
from dotenv import load_dotenv

load_dotenv()

def list_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY not set")
        return

    client = genai.Client(api_key=api_key)
    print("Listing available models...")
    for model in client.models.list():
        print(f"Model: {model.name}")
        # print(f"  Supported generation methods: {model.supported_generation_methods}")

if __name__ == "__main__":
    list_models()
