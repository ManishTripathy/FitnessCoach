# Fitness Coach App

An AI-powered fitness coaching application that helps users Observe, Decide, and Act on their fitness goals. Built with React, FastAPI, Firebase, and Google Gemini.

## Tech Stack

*   **Frontend**: React (Vite), TypeScript, Tailwind CSS, shadcn/ui
*   **Backend**: FastAPI (Python), Firebase Admin SDK
*   **Database**: Cloud Firestore
*   **AI**: Google Gemini (via Google Gen AI SDK & ADK)
*   **Tools**: Google Agent Development Kit (ADK) for advanced agentic workflows

## Project Structure

```
fitness_coach/
├── backend/                # FastAPI Backend
│   ├── api/                # API Routers (endpoints)
│   ├── core/               # Core config & dependencies
│   ├── scripts/            # Data seeding & maintenance scripts
│   ├── services/           # Business logic (AI, Firebase)
│   └── main.py             # Application entry point
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Application pages (Observe, Decide, Act)
│   │   └── services/       # API client
├── feature_prompts/        # Prompt engineering & test assets
├── plans/                  # Implementation plans
└── Makefile                # Task runner
```

## Prerequisites

*   Python 3.12+
*   Node.js & npm
*   Firebase Project & Service Account Credentials
*   Google Gemini API Key

## Setup

1.  **Clone the repository**
2.  **Environment Setup**:
    *   Create `.env` in `backend/` with:
        ```env
        GOOGLE_API_KEY=your_key
        FIREBASE_CREDENTIALS_PATH=path/to/credentials.json
        FIREBASE_STORAGE_BUCKET=your-bucket.appspot.com
        ```
3.  **Install Dependencies**:
    ```bash
    make setup
    ```

## Running the App

Start both backend and frontend:
```bash
make dev
```

Or run individually:
*   Backend: `make backend` (http://localhost:8000)
*   Frontend: `make frontend` (http://localhost:5173)

## Data Management & Seeding

### 1. Reset Database
Clear existing data from `workout_library` before fresh ingestion.
```bash
make reset-db
```

### 2. Seed Data
Populate the database with workout videos.

#### Option A: Standard Seeding (Videos Search)
Searches for videos directly. Good for broad coverage.
```bash
make seed-data
```

#### Option B: Agent-Curated Seeding (ADK + Playlist Search)
Uses a **Google ADK Agent** to find and curate *playlists* first. The Agent filters out vlogs, food content, and non-exercise playlists, ensuring only high-quality workout programs are ingested.

1.  **Agent**: Searches for playlists by the trainer.
2.  **Curation**: Filters playlists to keep only "Workout/Program" types.
3.  **Ingestion**: Extracts videos from the approved playlists.

```bash
make seed-data-agent
```

To specify trainers:
```bash
make seed-data-agent TRAINERS="'Jeff Nippard'" VIDEOS_PER_PLAYLIST=5
```
