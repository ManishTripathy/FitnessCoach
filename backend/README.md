# Fitness Coach Backend

## Setup

1.  **Install Dependencies**:
    Navigate to the project root directory and run:
    ```bash
    pip install -r backend/requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file in the `backend` directory.
    Copy `.env.example` to `.env` and fill in the required values (Firebase credentials path, API keys).
    ```bash
    cp backend/.env.example backend/.env
    ```

## Running the Server

To start the backend server, run the following command from the **project root directory** (`fitness_coach/`):

```bash
python -m uvicorn backend.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.
API documentation is available at `http://127.0.0.1:8000/docs`.
