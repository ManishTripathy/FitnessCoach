import os
from dotenv import load_dotenv

# Define BASE_DIR first to locate .env correctly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

class Settings:
    # Use absolute path for credentials to avoid path resolution issues
    BASE_DIR = BASE_DIR
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", os.path.join(BASE_DIR, "firebase-credentials.json"))
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

settings = Settings()
