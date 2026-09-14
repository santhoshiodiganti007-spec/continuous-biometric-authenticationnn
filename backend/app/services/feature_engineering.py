"""Feature engineering pipeline for keystroke and mouse behavioral biometrics."""

import math
from typing import List, Dict, Any, Tuple
import numpy as np


class BehavioralFeatureExtractor:
    """
    Extracts statistical and temporal behavioral biometrics from raw user interaction events.
    Computes both keystroke dynamics and mouse dynamics features.
    """

    FEATURE_NAMES = [
        # Keystroke features
        "keystroke_mean_hold_duration",
        "keystroke_std_hold_duration",
        "keystroke_mean_flight_time",
        "keystroke_var_flight_time",
        "keystroke_typing_speed",
        "keystroke_event_frequency",
        # Mouse movement features
        "mouse_mean_speed",
        "mouse_max_speed",
        "mouse_mean_acceleration",
        "mouse_total_distance",
        "mouse_direction_changes",
        # Mouse interaction features
        "mouse_click_frequency",
        "mouse_mean_click_duration",
        "mouse_scroll_frequency",
        # Cross-modal behavioral balance
        "keystroke_to_mouse_ratio",
        "activity_pause_rate"
    ]

    @classmethod
    def extract_window_features(
        cls,
        keystroke_events: List[Dict[str, Any]],
        mouse_events: List[Dict[str, Any]],
        window_duration_seconds: float = 10.0
    ) -> Dict[str, float]:
        """
        Calculates normalized statistical features across a time or count window.
        """
        features = {}

        # 1. Keystroke Dynamics Features
        if keystroke_events and len(keystroke_events) > 0:
            hold_times = [float(e.get("hold_duration", 0.0)) for e in keystroke_events]
            flight_times = [float(e.get("flight_time", 0.0)) for e in keystroke_events]
            
            features["keystroke_mean_hold_duration"] = float(np.mean(hold_times)) if hold_times else 0.0
            features["keystroke_std_hold_duration"] = float(np.std(hold_times)) if hold_times else 0.0
            features["keystroke_mean_flight_time"] = float(np.mean(flight_times)) if flight_times else 0.0
            features["keystroke_var_flight_time"] = float(np.var(flight_times)) if flight_times else 0.0
            
            # Typing speed in chars per second
            timestamps = [float(e.get("timestamp", 0.0)) for e in keystroke_events]
            time_span_s = max(0.5, (max(timestamps) - min(timestamps)) / 1000.0) if len(timestamps) > 1 else 1.0
            features["keystroke_typing_speed"] = float(len(keystroke_events) / time_span_s)
            features["keystroke_event_frequency"] = float(len(keystroke_events) / max(1.0, window_duration_seconds))
        else:
            features["keystroke_mean_hold_duration"] = 0.0
            features["keystroke_std_hold_duration"] = 0.0
            features["keystroke_mean_flight_time"] = 0.0
            features["keystroke_var_flight_time"] = 0.0
            features["keystroke_typing_speed"] = 0.0
            features["keystroke_event_frequency"] = 0.0

        # 2. Mouse Dynamics Features
        if mouse_events and len(mouse_events) > 0:
            speeds = [float(m.get("speed", 0.0)) for m in mouse_events]
            accelerations = [float(m.get("acceleration", 0.0)) for m in mouse_events]
            distances = [float(m.get("distance", 0.0)) for m in mouse_events]
            directions = [float(m.get("direction", 0.0)) for m in mouse_events]
            
            click_events = [m for m in mouse_events if m.get("event_type") in ("click", "dblclick", "mousedown")]
            click_durations = [float(m.get("click_duration", 0.0)) for m in click_events if float(m.get("click_duration", 0.0)) > 0]
            scroll_events = [m for m in mouse_events if m.get("event_type") == "scroll"]

            features["mouse_mean_speed"] = float(np.mean(speeds)) if speeds else 0.0
            features["mouse_max_speed"] = float(np.max(speeds)) if speeds else 0.0
            features["mouse_mean_acceleration"] = float(np.mean(accelerations)) if accelerations else 0.0
            features["mouse_total_distance"] = float(np.sum(distances)) if distances else 0.0

            # Direction changes (angular jitter/curvature)
            if len(directions) > 1:
                diffs = np.abs(np.diff(directions))
                # Wrap angle differences around pi
                diffs = np.where(diffs > np.pi, 2 * np.pi - diffs, diffs)
                features["mouse_direction_changes"] = float(np.mean(diffs))
            else:
                features["mouse_direction_changes"] = 0.0

            mouse_timestamps = [float(m.get("timestamp", 0.0)) for m in mouse_events]
            mouse_time_span_s = max(0.5, (max(mouse_timestamps) - min(mouse_timestamps)) / 1000.0) if len(mouse_timestamps) > 1 else 1.0
            
            features["mouse_click_frequency"] = float(len(click_events) / max(1.0, mouse_time_span_s))
            features["mouse_mean_click_duration"] = float(np.mean(click_durations)) if click_durations else 0.0
            features["mouse_scroll_frequency"] = float(len(scroll_events) / max(1.0, mouse_time_span_s))
        else:
            features["mouse_mean_speed"] = 0.0
            features["mouse_max_speed"] = 0.0
            features["mouse_mean_acceleration"] = 0.0
            features["mouse_total_distance"] = 0.0
            features["mouse_direction_changes"] = 0.0
            features["mouse_click_frequency"] = 0.0
            features["mouse_mean_click_duration"] = 0.0
            features["mouse_scroll_frequency"] = 0.0

        # 3. Cross-modal behavioral balance
        total_keys = len(keystroke_events)
        total_mouse = len(mouse_events)
        features["keystroke_to_mouse_ratio"] = float(total_keys / (total_mouse + 1e-5))
        features["activity_pause_rate"] = 0.0  # Computed if timeline gaps exceed threshold

        return features

    @classmethod
    def create_sliding_windows(
        cls,
        all_events: List[Dict[str, Any]],
        window_size: int = 40,
        overlap_ratio: float = 0.5
    ) -> List[Dict[str, float]]:
        """
        Creates sequential behavioral feature vectors using overlapping sliding windows.
        """
        if not all_events:
            return []

        # Sort combined events by timestamp
        sorted_events = sorted(all_events, key=lambda x: float(x.get("timestamp", 0)))
        step = max(1, int(window_size * (1.0 - overlap_ratio)))
        
        feature_windows = []
        for i in range(0, len(sorted_events) - window_size + 1, step):
            window_slice = sorted_events[i : i + window_size]
            keys = [e for e in window_slice if e.get("type") == "keystroke"]
            mouse = [e for e in window_slice if e.get("type") == "mouse"]
            
            t_start = float(window_slice[0].get("timestamp", 0))
            t_end = float(window_slice[-1].get("timestamp", 0))
            span_s = max(0.5, (t_end - t_start) / 1000.0)

            feats = cls.extract_window_features(keys, mouse, window_duration_seconds=span_s)
            feature_windows.append(feats)

        # If events are fewer than full window_size, create at least 1 feature vector if enough events exist
        if not feature_windows and len(sorted_events) >= 5:
            keys = [e for e in sorted_events if e.get("type") == "keystroke"]
            mouse = [e for e in sorted_events if e.get("type") == "mouse"]
            t_start = float(sorted_events[0].get("timestamp", 0))
            t_end = float(sorted_events[-1].get("timestamp", 0))
            span_s = max(0.5, (t_end - t_start) / 1000.0)
            feature_windows.append(cls.extract_window_features(keys, mouse, window_duration_seconds=span_s))

        return feature_windows

    @classmethod
    def feature_dict_to_vector(cls, feature_dict: Dict[str, float]) -> np.ndarray:
        """Converts feature dictionary to ordered numpy feature vector."""
        return np.array([feature_dict.get(name, 0.0) for name in cls.FEATURE_NAMES], dtype=np.float32)
