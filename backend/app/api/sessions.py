"""Session lifecycle endpoints for continuous behavioral tracking."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database_models import User, AuthenticationSession
from app.models.schemas import SessionStartRequest, SessionStopRequest, SessionOut
from app.utils.security import get_current_user
from app.services.authentication_service import ContinuousAuthService

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/start", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def start_tracking_session(
    payload: SessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new continuous biometric authentication session."""
    session = ContinuousAuthService.start_session(
        db=db,
        user=current_user,
        user_agent=payload.user_agent,
        screen_resolution=payload.screen_resolution
    )
    return session


@router.post("/stop", response_model=SessionOut)
def stop_tracking_session(
    payload: SessionStopRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Conclude an active continuous tracking session."""
    session = ContinuousAuthService.stop_session(
        db=db,
        session_id=payload.session_id,
        user_id=current_user.id
    )
    return session


@router.get("/{session_id}", response_model=SessionOut)
def get_session_details(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve metadata and status of an authentication session."""
    session = db.query(AuthenticationSession).filter(
        AuthenticationSession.id == session_id,
        AuthenticationSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session
