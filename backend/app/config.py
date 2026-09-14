"""Configuration settings for continuous biometric authentication backend."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Driven Continuous Authentication"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite:///./biometric_auth.db"
    
    # Security
    SECRET_KEY: str = "continuous-auth-super-secret-key-for-mtech-dissertation-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
        "*"
    ]
    
    # Machine Learning & Continuous Authentication
    MODEL_PATH: str = "ml/saved_models/best_transformer.pt"
    SCALER_PATH: str = "ml/saved_models/scaler.pkl"
    FEATURE_NAMES_PATH: str = "ml/saved_models/feature_names.json"
    
    # Continuous Authentication Thresholds (configurable)
    CONFIDENCE_THRESHOLD_LEGITIMATE: float = 0.80
    CONFIDENCE_THRESHOLD_SUSPICIOUS: float = 0.50
    
    # Sliding Window Configuration
    WINDOW_EVENT_SIZE: int = 40  # Number of raw events per behavioral window
    WINDOW_OVERLAP_RATIO: float = 0.5  # 50% overlap between consecutive windows
    
    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }


settings = Settings()
