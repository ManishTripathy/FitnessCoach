import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

settings = Settings()
