"""Explainability API providing feature importance rankings and model decision logic."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database_models import User, AuthenticationPrediction
from app.models.schemas import ExplainRequest, ExplainResponse, FeatureImportanceItem
from app.utils.security import get_current_user
from app.services.explainability_service import explainability_service

router = APIRouter(tags=["Explainable AI"])


@router.post("/explain", response_model=ExplainResponse)
def get_prediction_explanation(
    payload: ExplainRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns explainable AI diagnostics for the most recent session authentication decision.
    Ranks features by attribution magnitude and presents natural-language explanations.
    """
    latest_pred = db.query(AuthenticationPrediction).filter(
        AuthenticationPrediction.session_id == payload.session_id,
        AuthenticationPrediction.user_id == current_user.id
    ).order_by(AuthenticationPrediction.timestamp.desc()).first()

    if not latest_pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction records found for this session to explain."
        )

    top_features = latest_pred.top_features or []
    # Format into response
    items = [FeatureImportanceItem(**f) for f in top_features]

    summary = (
        f"Model classified session as {latest_pred.classification} with {latest_pred.probability * 100:.1f}% "
        f"confidence. Top contributing biometric cues: " +
        ", ".join([f.feature for f in items[:3]]) if items else "Baseline metrics normal."
    )

    return {
        "session_id": payload.session_id,
        "prediction": latest_pred.classification,
        "confidence": latest_pred.probability,
        "top_features": items,
        "summary": summary
    }
