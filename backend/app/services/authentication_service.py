"""Authentication service managing session state, event buffering, and continuous evaluation."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.database_models import (
    AuthenticationSession,
    KeystrokeEvent,
    MouseEvent,
    BehavioralFeatureWindow,
    AuthenticationPrediction,
    User
)
from app.services.feature_engineering import BehavioralFeatureExtractor
from app.services.model_service import model_service
from app.services.explainability_service import explainability_service
from app.config import settings


class ContinuousAuthService:
    """Orchestrates live continuous behavioral verification sessions."""

    @classmethod
    def start_session(
        cls,
        db: Session,
        user: User,
        user_agent: Optional[str] = None,
        screen_resolution: Optional[str] = None
    ) -> AuthenticationSession:
        """Initializes a new continuous tracking session."""
        session = AuthenticationSession(
            user_id=user.id,
            user_agent=user_agent,
            screen_resolution=screen_resolution,
            is_active=True,
            status="ACTIVE",
            start_time=datetime.utcnow(),
            total_events_count=0
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @classmethod
    def stop_session(cls, db: Session, session_id: str, user_id: str) -> AuthenticationSession:
        """Concludes an active authentication session."""
        session = db.query(AuthenticationSession).filter(
            AuthenticationSession.id == session_id,
            AuthenticationSession.user_id == user_id
        ).first()

        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        session.is_active = False
        session.end_time = datetime.utcnow()
        if session.status == "ACTIVE":
            session.status = "COMPLETED"
        db.commit()
        db.refresh(session)
        return session

    @classmethod
    def ingest_keystrokes(
        cls,
        db: Session,
        session_id: str,
        user_id: str,
        events: List[Any]
    ) -> int:
        """Stores a batch of keystroke dynamics events."""
        session = db.query(AuthenticationSession).filter(
            AuthenticationSession.id == session_id,
            AuthenticationSession.user_id == user_id
        ).first()
        if not session or not session.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active session required")

        db_events = []
        for e in events:
            db_events.append(
                KeystrokeEvent(
                    user_id=user_id,
                    session_id=session_id,
                    timestamp=e.timestamp,
                    press_time=e.press_time,
                    release_time=e.release_time,
                    hold_duration=e.hold_duration,
                    flight_time=e.flight_time,
                    key_category=e.key_category
                )
            )
        db.bulk_save_objects(db_events)
        session.total_events_count += len(events)
        db.commit()
        return len(events)

    @classmethod
    def ingest_mouse(
        cls,
        db: Session,
        session_id: str,
        user_id: str,
        events: List[Any]
    ) -> int:
        """Stores a batch of mouse telemetry events."""
        session = db.query(AuthenticationSession).filter(
            AuthenticationSession.id == session_id,
            AuthenticationSession.user_id == user_id
        ).first()
        if not session or not session.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active session required")

        db_events = []
        for e in events:
            db_events.append(
                MouseEvent(
                    user_id=user_id,
                    session_id=session_id,
                    timestamp=e.timestamp,
                    event_type=e.event_type,
                    x=e.x,
                    y=e.y,
                    speed=e.speed,
                    distance=e.distance,
                    direction=e.direction,
                    acceleration=e.acceleration,
                    click_duration=e.click_duration,
                    scroll_delta=e.scroll_delta
                )
            )
        db.bulk_save_objects(db_events)
        session.total_events_count += len(events)
        db.commit()
        return len(events)

    @classmethod
    def evaluate_recent_window(
        cls,
        db: Session,
        session_id: str,
        user_id: str,
        window_size: int = 40
    ) -> Dict[str, Any]:
        """
        Gathers recent keystroke and mouse events from the session, extracts features,
        runs Transformer inference, and records the authentication prediction.
        """
        # Fetch recent keystrokes
        keystrokes = db.query(KeystrokeEvent).filter(
            KeystrokeEvent.session_id == session_id
        ).order_by(KeystrokeEvent.timestamp.desc()).limit(window_size).all()

        # Fetch recent mouse events
        mouse_events = db.query(MouseEvent).filter(
            MouseEvent.session_id == session_id
        ).order_by(MouseEvent.timestamp.desc()).limit(window_size).all()

        # Combine and format events
        combined = []
        for k in keystrokes:
            combined.append({
                "type": "keystroke",
                "timestamp": k.timestamp,
                "hold_duration": k.hold_duration,
                "flight_time": k.flight_time
            })
        for m in mouse_events:
            combined.append({
                "type": "mouse",
                "timestamp": m.timestamp,
                "event_type": m.event_type,
                "speed": m.speed,
                "distance": m.distance,
                "direction": m.direction,
                "acceleration": m.acceleration,
                "click_duration": m.click_duration
            })

        # Extract behavioral feature vectors
        windows = BehavioralFeatureExtractor.create_sliding_windows(
            combined,
            window_size=min(window_size, max(len(combined), 5)),
            overlap_ratio=settings.WINDOW_OVERLAP_RATIO
        )

        if not windows:
            # Cold start baseline before sufficient interactions
            windows = [{name: 0.0 for name in BehavioralFeatureExtractor.FEATURE_NAMES}]

        # Run Transformer inference
        classification, confidence, attn_weights = model_service.evaluate_behavioral_window(windows)

        # Generate explainable feature attribution
        top_features = explainability_service.explain_prediction(windows[-1], attn_weights)

        # Record prediction in database
        prediction_record = AuthenticationPrediction(
            user_id=user_id,
            session_id=session_id,
            probability=confidence,
            classification=classification,
            top_features=top_features
        )
        db.add(prediction_record)

        # Record feature window in database
        window_record = BehavioralFeatureWindow(
            user_id=user_id,
            session_id=session_id,
            window_start_time=combined[-1]["timestamp"] if combined else 0.0,
            window_end_time=combined[0]["timestamp"] if combined else 0.0,
            event_count=len(combined),
            features_data=windows[-1]
        )
        db.add(window_record)
        db.commit()

        # Check if session should be flagged or terminated
        if classification == "POTENTIAL INTRUDER":
            session = db.query(AuthenticationSession).filter(AuthenticationSession.id == session_id).first()
            if session:
                session.status = "FLAGGED_INTRUSION"
                db.commit()

        return {
            "session_id": session_id,
            "prediction": classification,
            "confidence": confidence,
            "is_legitimate": classification == "LEGITIMATE USER",
            "timestamp": datetime.utcnow(),
            "important_features": top_features,
            "attention_weights": attn_weights,
            "status_message": f"Biometric verification successful. User status: {classification}"
        }
