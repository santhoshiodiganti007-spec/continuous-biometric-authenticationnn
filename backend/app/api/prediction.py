"""Continuous prediction endpoints using the Explainable Transformer model."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database_models import User, AuthenticationPrediction
from app.models.schemas import PredictRequest, PredictResponse, PredictionHistoryOut
from app.utils.security import get_current_user
from app.services.authentication_service import ContinuousAuthService

router = APIRouter(tags=["Continuous Authentication"])


@router.post("/predict", response_model=PredictResponse)
def predict_continuous_authentication(
    payload: PredictRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes continuous verification on the active session's sliding event window.
    Applies the Transformer model to compute confidence and determine user status.
    """
    result = ContinuousAuthService.evaluate_recent_window(
        db=db,
        session_id=payload.session_id,
        user_id=current_user.id
    )
    return result


@router.get("/predictions/history", response_model=List[PredictionHistoryOut])
def get_prediction_history(
    session_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves chronological verification scores for timeline plotting."""
    records = db.query(AuthenticationPrediction).filter(
        AuthenticationPrediction.session_id == session_id,
        AuthenticationPrediction.user_id == current_user.id
    ).order_by(AuthenticationPrediction.timestamp.asc()).limit(limit).all()
    return records
