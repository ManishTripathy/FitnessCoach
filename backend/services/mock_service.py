import os
import json
import datetime
from typing import Optional
from backend.core.config import settings

def try_get_mock_plan(log_tag: str) -> Optional[dict]:
    """
    Attempts to load a mock plan if USE_MOCK_PLAN is enabled.
    Returns the plan dictionary if successful, None otherwise.
    """
    if not settings.USE_MOCK_PLAN:
        return None

    try:
        print(f"[{datetime.datetime.utcnow().isoformat()}] MODE: MOCK - Generating {log_tag} Plan")
        mock_path = os.path.join(settings.BASE_DIR, "mock_responses/plan.json")
        with open(mock_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading mock plan: {e}")
        return None
