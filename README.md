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
