import logging
from typing import Optional

import firebase_admin
from firebase_admin import auth as firebase_auth
from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


def verify_firebase_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    if not firebase_admin._apps:
        raise HTTPException(status_code=503, detail="Firebase Admin SDK not initialized")

    id_token = authorization.split(" ", 1)[1].strip()
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception as exc:
        logger.warning("Token verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token")
