"""Preprocessing and normalization helpers for behavioral feature vectors."""

import numpy as np
from typing import List, Dict, Any


class BehavioralPreprocessor:
    """Scales and pads sequential behavioral feature vectors for Transformer model input."""

    def __init__(self, means: np.ndarray = None, stds: np.ndarray = None):
        self.means = means
        self.stds = stds

    def fit(self, feature_matrix: np.ndarray):
        """Fit normalization parameters (mean and standard deviation)."""
        self.means = np.mean(feature_matrix, axis=0)
        self.stds = np.std(feature_matrix, axis=0)
        # Avoid division by zero
        self.stds[self.stds < 1e-5] = 1.0

    def transform(self, feature_matrix: np.ndarray) -> np.ndarray:
        """Standardize feature matrix."""
        if self.means is None or self.stds is None:
            # Fallback zero-mean unit-variance default
            return np.clip(feature_matrix, -10.0, 10.0)
        norm = (feature_matrix - self.means) / self.stds
        return np.clip(norm, -10.0, 10.0)

    def fit_transform(self, feature_matrix: np.ndarray) -> np.ndarray:
        self.fit(feature_matrix)
        return self.transform(feature_matrix)
