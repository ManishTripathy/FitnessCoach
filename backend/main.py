from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import connectivity

app = FastAPI(title="Fitness Coach API", description="Backend for Fitness Coach Application")

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

@app.get("/")
async def root():
    return {"status": "ok", "message": "Fitness Coach Backend Running. Go to /docs for API documentation."}
