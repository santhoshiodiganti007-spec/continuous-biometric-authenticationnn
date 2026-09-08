"""Pydantic schemas for request validation and response serialization."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# --- Authentication & User Schemas ---

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None


# --- Session Tracking Schemas ---

class SessionStartRequest(BaseModel):
    user_agent: Optional[str] = None
    screen_resolution: Optional[str] = None


class SessionStopRequest(BaseModel):
    session_id: str


class SessionOut(BaseModel):
    id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    is_active: bool
    status: str
    total_events_count: int

    model_config = {"from_attributes": True}


# --- Behavioral Event Ingestion Schemas ---

class KeystrokeEventItem(BaseModel):
    timestamp: float
    press_time: float
    release_time: float
    hold_duration: float
    flight_time: float
    key_category: Optional[str] = "ALPHANUMERIC"


class KeystrokeBatchRequest(BaseModel):
    session_id: str
    events: List[KeystrokeEventItem]


class MouseEventItem(BaseModel):
    timestamp: float
    event_type: str  # move, click, dblclick, scroll
    x: float
    y: float
    speed: float = 0.0
    distance: float = 0.0
    direction: float = 0.0
    acceleration: float = 0.0
    click_duration: float = 0.0
    scroll_delta: float = 0.0


class MouseBatchRequest(BaseModel):
    session_id: str
    events: List[MouseEventItem]


# --- Continuous Inference & Explainability Schemas ---

class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
    value: Optional[float] = None
    description: Optional[str] = None


class PredictRequest(BaseModel):
    session_id: str
    events: Optional[List[Dict[str, Any]]] = None  # Optional client-computed window or triggered by recent session events


class PredictResponse(BaseModel):
    session_id: str
    prediction: str  # LEGITIMATE USER, SUSPICIOUS USER, POTENTIAL INTRUDER
    confidence: float
    is_legitimate: bool
    timestamp: datetime
    important_features: List[FeatureImportanceItem]
    attention_weights: Optional[List[float]] = None
    status_message: str


class ExplainRequest(BaseModel):
    session_id: str
    features: Optional[Dict[str, float]] = None


class ExplainResponse(BaseModel):
    session_id: str
    prediction: str
    confidence: float
    top_features: List[FeatureImportanceItem]
    summary: str


class PredictionHistoryOut(BaseModel):
    id: str
    session_id: str
    timestamp: datetime
    probability: float
    classification: str
    top_features: Optional[List[Dict[str, Any]]] = None

    model_config = {"from_attributes": True}
