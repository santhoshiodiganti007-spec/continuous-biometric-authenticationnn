"""Endpoints for streaming batches of raw behavioral biometrics events."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database_models import User
from app.models.schemas import KeystrokeBatchRequest, MouseBatchRequest
from app.utils.security import get_current_user
from app.services.authentication_service import ContinuousAuthService

router = APIRouter(prefix="/behavior", tags=["Behavioral Biometrics"])


@router.post("/keystrokes", status_code=status.HTTP_200_OK)
def ingest_keystroke_batch(
    payload: KeystrokeBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ingest a batch of keystroke timing dynamics.
    Stores timestamps and hold/flight times without sensitive character content.
    """
    count = ContinuousAuthService.ingest_keystrokes(
        db=db,
        session_id=payload.session_id,
        user_id=current_user.id,
        events=payload.events
    )
    return {
        "status": "success",
        "ingested_count": count,
        "session_id": payload.session_id
    }


@router.post("/mouse", status_code=status.HTTP_200_OK)
def ingest_mouse_batch(
    payload: MouseBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ingest a batch of mouse kinematic telemetry events.
    Stores speed, acceleration, distance, clicks, and scroll metrics.
    """
    count = ContinuousAuthService.ingest_mouse(
        db=db,
        session_id=payload.session_id,
        user_id=current_user.id,
        events=payload.events
    )
    return {
        "status": "success",
        "ingested_count": count,
        "session_id": payload.session_id
    }
