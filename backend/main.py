from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.api import connectivity
from backend.services.firebase_service import initialize_firebase

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Firebase
    print("Initializing Firebase...")
    if initialize_firebase():
        print("Firebase initialized successfully")
    else:
        print("Failed to initialize Firebase")
    yield
    # Shutdown logic if needed

app = FastAPI(title="Fitness Coach API", description="Backend for Fitness Coach Application", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(connectivity.router, prefix="/api/v1", tags=["connectivity"])
from backend.api.routers import observe, decide
app.include_router(observe.router, prefix="/api/v1", tags=["observe"])
app.include_router(decide.router, prefix="/api/v1", tags=["decide"])


@app.get("/")
async def root():
    return {"status": "ok", "message": "Fitness Coach Backend Running. Go to /docs for API documentation."}
