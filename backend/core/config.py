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
    USE_MOCK_PLAN = os.getenv("USE_MOCK_PLAN", "false").lower() == "true"
    USE_MOCK_ANALYZE = os.getenv("USE_MOCK_ANALYZE", "false").lower() == "true"
    USE_MOCK_SUGGEST = os.getenv("USE_MOCK_SUGGEST", "false").lower() == "true"
    USE_MOCK_GENERATE = os.getenv("USE_MOCK_GENERATE", "false").lower() == "true"

settings = Settings()
