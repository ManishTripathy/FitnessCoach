# Fitness Coach Backend

## Setup

### 1. Create and Activate Virtual Environment
It is recommended to use a virtual environment to manage dependencies. Run the following commands from the **project root directory** (`fitness_coach/`):

```bash
# Create virtual environment (one time only)
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 2. Install Dependencies
With the virtual environment activated, install the required packages:

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the **project root directory** or `backend/` directory.
Copy `.env.example` to `.env` and fill in the required values (Firebase credentials path, API keys).

```bash
cp backend/.env.example .env
```

## Running the Server

To start the backend server, ensure your virtual environment is activated, then run the following command from the **project root directory**:

```bash
# Activate venv if not already active
source venv/bin/activate

# Start the server
uvicorn backend.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.
API documentation is available at `http://127.0.0.1:8000/docs`.

### Verifying Python Version
To verify which Python version your virtual environment is using:

```bash
source venv/bin/activate
python --version
which python  # Should point to .../fitness_coach/venv/bin/python
```


The below command was used to update python in venv from inside the backend directory
```
source $HOME/.local/bin/env && uv python install 3.12 && uv venv venv --python 3.12 && source venv/bin/activate && uv pip install -r requirements.txt
```