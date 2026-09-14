"""Dataset builder module for continuous behavioral biometric authentication."""

import os
import json
import random
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from app.services.feature_engineering import BehavioralFeatureExtractor


class BehavioralDatasetBuilder:
    """
    Constructs train, validation, and test datasets for the Transformer model.
    Enforces strict session-based isolation to prevent data leakage between splits.
    """

    FEATURE_NAMES = BehavioralFeatureExtractor.FEATURE_NAMES

    @classmethod
    def generate_synthetic_research_benchmark(
        cls,
        num_legitimate_sessions: int = 25,
        num_impostor_sessions: int = 25,
        windows_per_session: int = 30,
        random_seed: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Synthesizes realistic biometric interaction sessions based on empirical behavioral distributions.
        - Legitimate User: Consistent key hold duration (~95ms, std ~12ms), steady typing cadence,
          smooth cursor trajectory, low angular jitter, steady click hold.
        - Impostors: Erratic hold durations (~160ms, std ~45ms), longer irregular flight times,
          abrupt jerky mouse speed spikes, high directional changes.
        
        Returns:
            X_train, y_train, X_val, y_val, X_test, y_test
        """
        np.random.seed(random_seed)
        random.seed(random_seed)

        # Baseline parameters for legitimate profile
        legit_profile = {
            "keystroke_mean_hold_duration": (95.0, 10.0),
            "keystroke_std_hold_duration": (12.0, 3.0),
            "keystroke_mean_flight_time": (130.0, 15.0),
            "keystroke_var_flight_time": (400.0, 80.0),
            "keystroke_typing_speed": (4.5, 0.6),
            "keystroke_event_frequency": (3.8, 0.5),
            "mouse_mean_speed": (1.2, 0.2),
            "mouse_max_speed": (3.5, 0.5),
            "mouse_mean_acceleration": (0.4, 0.1),
            "mouse_total_distance": (1800.0, 250.0),
            "mouse_direction_changes": (0.35, 0.08),
            "mouse_click_frequency": (0.4, 0.1),
            "mouse_mean_click_duration": (80.0, 10.0),
            "mouse_scroll_frequency": (0.2, 0.05),
            "keystroke_to_mouse_ratio": (1.1, 0.2),
            "activity_pause_rate": (0.05, 0.02)
        }

        # Impostor profiles with distinctive anomalies
        impostor_profiles = [
            # Impostor A: Hesitant, slow typer, erratic mouse
            {
                "keystroke_mean_hold_duration": (170.0, 25.0),
                "keystroke_std_hold_duration": (48.0, 12.0),
                "keystroke_mean_flight_time": (280.0, 40.0),
                "keystroke_var_flight_time": (1800.0, 300.0),
                "keystroke_typing_speed": (2.1, 0.4),
                "keystroke_event_frequency": (1.8, 0.3),
                "mouse_mean_speed": (2.6, 0.5),
                "mouse_max_speed": (7.0, 1.2),
                "mouse_mean_acceleration": (1.2, 0.3),
                "mouse_total_distance": (3200.0, 500.0),
                "mouse_direction_changes": (0.85, 0.15),
                "mouse_click_frequency": (0.15, 0.05),
                "mouse_mean_click_duration": (130.0, 25.0),
                "mouse_scroll_frequency": (0.5, 0.1),
                "keystroke_to_mouse_ratio": (0.4, 0.1),
                "activity_pause_rate": (0.25, 0.06)
            },
            # Impostor B: Fast erratic gamer-like jerky movement
            {
                "keystroke_mean_hold_duration": (70.0, 18.0),
                "keystroke_std_hold_duration": (30.0, 8.0),
                "keystroke_mean_flight_time": (85.0, 20.0),
                "keystroke_var_flight_time": (950.0, 150.0),
                "keystroke_typing_speed": (6.5, 1.0),
                "keystroke_event_frequency": (5.5, 0.8),
                "mouse_mean_speed": (3.4, 0.6),
                "mouse_max_speed": (9.2, 1.5),
                "mouse_mean_acceleration": (1.8, 0.4),
                "mouse_total_distance": (4100.0, 600.0),
                "mouse_direction_changes": (1.10, 0.20),
                "mouse_click_frequency": (1.2, 0.3),
                "mouse_mean_click_duration": (55.0, 12.0),
                "mouse_scroll_frequency": (0.8, 0.2),
                "keystroke_to_mouse_ratio": (1.9, 0.3),
                "activity_pause_rate": (0.02, 0.01)
            }
        ]

        def sample_session_windows(profile_dict, n_windows, label_val):
            session_windows = []
            for _ in range(n_windows):
                window_feats = []
                for fname in cls.FEATURE_NAMES:
                    mean_val, std_val = profile_dict[fname]
                    # Sample with small temporal noise
                    val = max(0.001, np.random.normal(mean_val, std_val))
                    window_feats.append(val)
                session_windows.append(window_feats)
            return np.array(session_windows, dtype=np.float32), np.full(n_windows, label_val, dtype=np.float32)

        # Build sessions
        legit_sessions = [sample_session_windows(legit_profile, windows_per_session, 1.0) for _ in range(num_legitimate_sessions)]
        impostor_sessions = [sample_session_windows(random.choice(impostor_profiles), windows_per_session, 0.0) for _ in range(num_impostor_sessions)]

        # Session-isolated train / val / test splitting (60% train, 20% val, 20% test)
        random.shuffle(legit_sessions)
        random.shuffle(impostor_sessions)

        def split_sessions(sessions_list):
            n = len(sessions_list)
            n_train = int(n * 0.6)
            n_val = int(n * 0.2)
            train_s = sessions_list[:n_train]
            val_s = sessions_list[n_train : n_train + n_val]
            test_s = sessions_list[n_train + n_val :]
            return train_s, val_s, test_s

        legit_tr, legit_val, legit_te = split_sessions(legit_sessions)
        imp_tr, imp_val, imp_te = split_sessions(impostor_sessions)

        def aggregate_splits(legit_part, imp_part):
            all_s = legit_part + imp_part
            random.shuffle(all_s)
            X = np.concatenate([s[0] for s in all_s], axis=0)
            y = np.concatenate([s[1] for s in all_s], axis=0)
            return X, y

        X_train, y_train = aggregate_splits(legit_tr, imp_tr)
        X_val, y_val = aggregate_splits(legit_val, imp_val)
        X_test, y_test = aggregate_splits(legit_te, imp_te)

        return X_train, y_train, X_val, y_val, X_test, y_test


if __name__ == "__main__":
    X_tr, y_tr, X_v, y_v, X_te, y_te = BehavioralDatasetBuilder.generate_synthetic_research_benchmark()
    print(f"Dataset generated successfully.")
    print(f"Train set: {X_tr.shape}, Labels: {y_tr.shape} (Legitimate: {np.sum(y_tr == 1)}, Impostor: {np.sum(y_tr == 0)})")
    print(f"Val set:   {X_v.shape}, Labels: {y_v.shape}")
    print(f"Test set:  {X_te.shape}, Labels: {y_te.shape}")
