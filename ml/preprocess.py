"""Preprocessing utilities for ML dataset normalization and serialization."""

import os
import pickle
import numpy as np
from app.utils.preprocessing import BehavioralPreprocessor


def prepare_and_normalize_data(X_train, X_val, X_test, save_dir="ml/saved_models"):
    """
    Fits standard normalizer on train split only and transforms val and test splits.
    Saves scaler parameters to disk for production inference.
    """
    os.makedirs(save_dir, exist_ok=True)
    scaler = BehavioralPreprocessor()
    X_train_norm = scaler.fit_transform(X_train)
    X_val_norm = scaler.transform(X_val)
    X_test_norm = scaler.transform(X_test)

    scaler_path = os.path.join(save_dir, "scaler.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump({"means": scaler.means, "stds": scaler.stds}, f)

    return X_train_norm, X_val_norm, X_test_norm, scaler
