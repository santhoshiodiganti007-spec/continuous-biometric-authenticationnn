"""SQLAlchemy models for continuous behavioral biometric authentication."""

from datetime import datetime
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship("AuthenticationSession", back_populates="user", cascade="all, delete-orphan")
    keystroke_events = relationship("KeystrokeEvent", back_populates="user", cascade="all, delete-orphan")
    mouse_events = relationship("MouseEvent", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("AuthenticationPrediction", back_populates="user", cascade="all, delete-orphan")


class AuthenticationSession(Base):
    """Continuous authentication tracking session."""
    __tablename__ = "authentication_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    status = Column(String(30), default="ACTIVE")  # ACTIVE, COMPLETED, TERMINATED_SUSPICIOUS
    user_agent = Column(String(255), nullable=True)
    screen_resolution = Column(String(50), nullable=True)
    total_events_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="sessions")
    keystroke_events = relationship("KeystrokeEvent", back_populates="session", cascade="all, delete-orphan")
    mouse_events = relationship("MouseEvent", back_populates="session", cascade="all, delete-orphan")
    feature_windows = relationship("BehavioralFeatureWindow", back_populates="session", cascade="all, delete-orphan")
    predictions = relationship("AuthenticationPrediction", back_populates="session", cascade="all, delete-orphan")


class KeystrokeEvent(Base):
    """
    Keystroke dynamics timing event.
    Stores timing and behavioral dynamics without sensitive character data.
    """
    __tablename__ = "keystroke_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("authentication_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(Float, nullable=False)  # High resolution millisecond timestamp
    press_time = Column(Float, nullable=False)
    release_time = Column(Float, nullable=False)
    hold_duration = Column(Float, nullable=False)  # In milliseconds
    flight_time = Column(Float, nullable=False)    # Time elapsed from previous key release
    key_category = Column(String(30), default="ALPHANUMERIC")  # ALPHANUMERIC, MODIFIER, SPACE, BACKSPACE, ENTER

    # Relationships
    user = relationship("User", back_populates="keystroke_events")
    session = relationship("AuthenticationSession", back_populates="keystroke_events")


class MouseEvent(Base):
    """
    Mouse dynamics telemetry event.
    Tracks speed, distance, trajectory, acceleration, clicks and scrolls.
    """
    __tablename__ = "mouse_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("authentication_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(Float, nullable=False)
    event_type = Column(String(20), nullable=False)  # move, click, dblclick, scroll
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    speed = Column(Float, default=0.0)             # Pixels per ms
    distance = Column(Float, default=0.0)          # Euclidean distance from prev point
    direction = Column(Float, default=0.0)         # Angle in radians (-pi to pi)
    acceleration = Column(Float, default=0.0)      # Rate of change of speed
    click_duration = Column(Float, default=0.0)    # Press to release time in ms (for clicks)
    scroll_delta = Column(Float, default=0.0)

    # Relationships
    user = relationship("User", back_populates="mouse_events")
    session = relationship("AuthenticationSession", back_populates="mouse_events")


class BehavioralFeatureWindow(Base):
    """
    Computed sequential feature windows extracted from behavioral streams.
    """
    __tablename__ = "behavioral_feature_windows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("authentication_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    window_start_time = Column(Float, nullable=False)
    window_end_time = Column(Float, nullable=False)
    event_count = Column(Integer, nullable=False)
    features_data = Column(JSON, nullable=False)  # Vector of engineered features as JSON

    # Relationships
    session = relationship("AuthenticationSession", back_populates="feature_windows")


class AuthenticationPrediction(Base):
    """
    Continuous authentication inference outcome generated by the Transformer model.
    """
    __tablename__ = "authentication_predictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("authentication_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    probability = Column(Float, nullable=False)  # Model confidence 0.0 - 1.0
    classification = Column(String(30), nullable=False)  # LEGITIMATE, SUSPICIOUS, POTENTIAL INTRUDER
    top_features = Column(JSON, nullable=True)  # SHAP/Attention feature importance breakdown

    # Relationships
    user = relationship("User", back_populates="predictions")
    session = relationship("AuthenticationSession", back_populates="predictions")
