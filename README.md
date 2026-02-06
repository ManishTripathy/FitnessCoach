# Fitness Coach App

## Project Structure
- `backend/`: FastAPI backend
- `frontend/`: React frontend

## Getting Started

### Prerequisites
- Python 3.12+ (managed via `uv`)
- Node.js & npm

### Setup
Run the following command from the project root to set up both backend (virtual env) and frontend (node modules):

```bash
make setup
```

### Running the App

You can run the backend and frontend using `make` commands from the project root.

**Option 1: Run both in parallel (Recommended)**
```bash
make dev
```

**Option 2: Run separately in different terminals**

Terminal 1 (Backend):
```bash
make backend
```

Terminal 2 (Frontend):
```bash
make frontend
```

### Manual Startup (Without Makefile)

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## Data Ingestion & Semantic Search

### Ingestion Architecture
The data ingestion pipeline (`backend/scripts/seed_workouts_v2.py`) works as follows:
1.  **Source**: Fetches workout videos from YouTube using `youtube-search-python` based on trainer names.
2.  **Processing**:
    -   Extracts metadata: Title, URL, Duration, Thumbnail.
    -   Normalizes duration to minutes.
    -   Infers workout focus (Legs, Abs, HIIT, etc.) from titles.
3.  **Embedding Generation**:
    -   Uses Google Gemini's `text-embedding-004` model via `ai_service.py`.
    -   Generates a vector embedding for the combined string of `Title + Description + Tags`.
4.  **Storage**: Saves the structured workout object (including the embedding vector) to Firestore in the `workout_library` collection.

### Semantic Search & Embeddings
-   **Embeddings**: High-dimensional vector representations of text. They capture semantic meaning (e.g., "build muscle" is semantically close to "hypertrophy" or "strength training").
-   **Usage**: When a user generates a workout plan, their goal (e.g., "I want to get lean") is embedded using the same model.
-   **Retrieval**: The system performs a vector similarity search (cosine similarity) in Firestore to find workouts that best match the user's intent, even if they don't share exact keywords.

### How to Seed Data
Run the following command to seed data for default trainers (Caroline Girvan, Sydney Cummings):
```bash
make seed-data
```

To specify different trainers or limits:
```bash
make seed-data TRAINERS="'Trainer A' 'Trainer B'" LIMIT=10
```
