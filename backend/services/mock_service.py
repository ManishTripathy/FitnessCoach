import os
import json
import datetime
from typing import Optional
from backend.core.config import settings

def _load_mock_json(filename: str, log_tag: str, endpoint_type: str) -> Optional[dict]:
    try:
        print(f"[{datetime.datetime.utcnow().isoformat()}] MODE: MOCK - {endpoint_type} ({log_tag})")
        mock_path = os.path.join(settings.BASE_DIR, f"mock_responses/{filename}")
        with open(mock_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading mock {filename}: {e}")
        return None

def try_get_mock_plan(log_tag: str) -> Optional[dict]:
    if not settings.USE_MOCK_PLAN:
        return None
    return _load_mock_json("plan.json", log_tag, "Generating Plan")

def try_get_mock_analyze(log_tag: str) -> Optional[dict]:
    if not settings.USE_MOCK_ANALYZE:
        return None
    return _load_mock_json("analyze.json", log_tag, "Analyzing Body")

def try_get_mock_suggest(log_tag: str) -> Optional[dict]:
    if not settings.USE_MOCK_SUGGEST:
        return None
    return _load_mock_json("suggest.json", log_tag, "Suggesting Path")

def try_get_mock_generate(log_tag: str) -> Optional[dict]:
    if not settings.USE_MOCK_GENERATE:
        return None
    return _load_mock_json("generate.json", log_tag, "Generating Physique")
