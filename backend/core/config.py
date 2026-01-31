import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Use absolute path for credentials to avoid path resolution issues
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", os.path.join(BASE_DIR, "firebase-credentials.json"))
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

settings = Settings()
