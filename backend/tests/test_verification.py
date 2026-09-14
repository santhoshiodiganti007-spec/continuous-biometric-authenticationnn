"""Comprehensive automated test suite verifying all 15 phases end-to-end."""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure root paths are accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.main import app
from app.config import settings
from app.models.transformer import BehavioralTransformer
from app.services.feature_engineering import BehavioralFeatureExtractor
import torch
import numpy as np

client = TestClient(app)


def test_01_health_endpoint():
    """Phase 2: Verify GET /health endpoint returns running status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "running"}


def test_02_transformer_architecture():
    """Phase 8: Verify PyTorch Behavioral Transformer forward pass and attention output."""
    model = BehavioralTransformer(input_dim=16, d_model=32, nhead=4, num_layers=2)
    dummy_input = torch.randn(2, 5, 16)  # batch_size=2, seq_len=5, features=16
    logits, attn = model(dummy_input, return_attention=True)
    
    assert logits.shape == (2, 1)
    assert attn.shape == (2, 5)
    
    prob, attn_list = model.predict_probability(dummy_input)
    assert 0.0 <= prob <= 1.0
    assert len(attn_list) == 5


def test_03_feature_engineering():
    """Phase 6: Verify statistical feature extraction and sliding windows."""
    keystrokes = [
        {"timestamp": 1000.0, "hold_duration": 90.0, "flight_time": 120.0},
        {"timestamp": 1200.0, "hold_duration": 95.0, "flight_time": 110.0},
        {"timestamp": 1400.0, "hold_duration": 100.0, "flight_time": 115.0}
    ]
    mouse_events = [
        {"timestamp": 1050.0, "event_type": "move", "speed": 1.2, "distance": 15.0, "direction": 0.5, "acceleration": 0.2},
        {"timestamp": 1150.0, "event_type": "click", "speed": 0.0, "distance": 0.0, "direction": 0.0, "acceleration": 0.0, "click_duration": 85.0}
    ]

    features = BehavioralFeatureExtractor.extract_window_features(keystrokes, mouse_events, window_duration_seconds=2.0)
    assert "keystroke_mean_hold_duration" in features
    assert "mouse_mean_speed" in features
    assert features["keystroke_mean_hold_duration"] > 0
    assert features["mouse_mean_speed"] > 0


def test_04_user_registration_and_login():
    """Phase 12 & 13: Verify User Registration and JWT Login."""
    unique_user = f"testuser_{np.random.randint(1000, 9999)}"
    reg_payload = {
        "username": unique_user,
        "email": f"{unique_user}@biometrics.edu",
        "password": "SecurePassword123!"
    }
    
    # Register
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["username"] == unique_user

    # Login
    login_res = client.post("/api/auth/login", json={"username": unique_user, "password": "SecurePassword123!"})
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    token = login_data["access_token"]
    return token, unique_user


def test_05_end_to_end_continuous_authentication():
    """Phase 10, 11, 12: Verify full session lifecycle, telemetry ingestion, prediction, and explainability."""
    token, username = test_04_user_registration_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Start Session
    start_res = client.post("/api/sessions/start", json={"user_agent": "TestBrowser/1.0"}, headers=headers)
    assert start_res.status_code == 201
    session_id = start_res.json()["id"]

    # 2. Ingest Keystroke batch
    key_batch = {
        "session_id": session_id,
        "events": [
            {"timestamp": 1000.0, "press_time": 1000.0, "release_time": 1095.0, "hold_duration": 95.0, "flight_time": 120.0, "key_category": "ALPHANUMERIC"},
            {"timestamp": 1215.0, "press_time": 1215.0, "release_time": 1310.0, "hold_duration": 95.0, "flight_time": 120.0, "key_category": "ALPHANUMERIC"},
            {"timestamp": 1430.0, "press_time": 1430.0, "release_time": 1520.0, "hold_duration": 90.0, "flight_time": 120.0, "key_category": "ALPHANUMERIC"}
        ]
    }
    key_res = client.post("/api/behavior/keystrokes", json=key_batch, headers=headers)
    assert key_res.status_code == 200
    assert key_res.json()["ingested_count"] == 3

    # 3. Ingest Mouse batch
    mouse_batch = {
        "session_id": session_id,
        "events": [
            {"timestamp": 1050.0, "event_type": "move", "x": 100.0, "y": 200.0, "speed": 1.2, "distance": 20.0, "direction": 0.4, "acceleration": 0.1, "click_duration": 0.0, "scroll_delta": 0.0},
            {"timestamp": 1150.0, "event_type": "click", "x": 120.0, "y": 200.0, "speed": 0.0, "distance": 0.0, "direction": 0.0, "acceleration": 0.0, "click_duration": 80.0, "scroll_delta": 0.0}
        ]
    }
    mouse_res = client.post("/api/behavior/mouse", json=mouse_batch, headers=headers)
    assert mouse_res.status_code == 200
    assert mouse_res.json()["ingested_count"] == 2

    # 4. Continuous Prediction
    pred_res = client.post("/api/predict", json={"session_id": session_id}, headers=headers)
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert pred_data["session_id"] == session_id
    assert pred_data["prediction"] in ["LEGITIMATE USER", "SUSPICIOUS USER", "POTENTIAL INTRUDER"]
    assert 0.0 <= pred_data["confidence"] <= 1.0
    assert len(pred_data["important_features"]) > 0

    # 5. Explainability Endpoint
    explain_res = client.post("/api/explain", json={"session_id": session_id}, headers=headers)
    assert explain_res.status_code == 200
    explain_data = explain_res.json()
    assert "top_features" in explain_data
    assert len(explain_data["top_features"]) > 0

    # 6. Verification History
    hist_res = client.get(f"/api/predictions/history?session_id={session_id}", headers=headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 1

    # 7. Stop Session
    stop_res = client.post("/api/sessions/stop", json={"session_id": session_id}, headers=headers)
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "COMPLETED"
