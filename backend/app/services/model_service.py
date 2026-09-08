"""Model service managing Transformer inference and status categorization."""

import os
import json
import logging
from typing import Tuple, List, Dict, Any, Optional
import torch
import numpy as np

from app.config import settings
from app.models.transformer import BehavioralTransformer
from app.services.feature_engineering import BehavioralFeatureExtractor
from app.utils.preprocessing import BehavioralPreprocessor

logger = logging.getLogger("model_service")


class ModelService:
    """Singleton service for continuous behavioral inference."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[BehavioralTransformer] = None
        self.preprocessor: Optional[BehavioralPreprocessor] = None
        self.feature_names = BehavioralFeatureExtractor.FEATURE_NAMES
        self.input_dim = len(self.feature_names)
        self.load_model()
        self._initialized = True

    def load_model(self):
        """Loads trained Transformer checkpoint or initializes a benchmark instance."""
        self.model = BehavioralTransformer(
            input_dim=self.input_dim,
            d_model=64,
            nhead=4,
            num_layers=2,
            dim_feedforward=128,
            dropout=0.1
        ).to(self.device)

        # Check if saved model checkpoint exists
        if os.path.exists(settings.MODEL_PATH):
            try:
                checkpoint = torch.load(settings.MODEL_PATH, map_location=self.device, weights_only=False)
                if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    self.model.load_state_dict(checkpoint["model_state_dict"])
                    means = checkpoint.get("scaler_means")
                    stds = checkpoint.get("scaler_stds")
                    if means is not None and stds is not None:
                        self.preprocessor = BehavioralPreprocessor(means=means, stds=stds)
                else:
                    self.model.load_state_dict(checkpoint)
                self.model.eval()
                logger.info(f"Loaded trained Transformer checkpoint from {settings.MODEL_PATH}")
                return
            except Exception as e:
                logger.warning(f"Could not load checkpoint ({e}). Using initialized model.")

        # Default fallback initialization
        self.model.eval()
        self.preprocessor = BehavioralPreprocessor()
        logger.info("Initialized default Behavioral Transformer model.")

    def evaluate_behavioral_window(
        self,
        feature_vectors: List[Dict[str, float]]
    ) -> Tuple[str, float, List[float]]:
        """
        Executes Transformer inference on sequential feature vectors.
        Returns:
            classification: (LEGITIMATE USER, SUSPICIOUS USER, POTENTIAL INTRUDER)
            confidence: float (0.0 to 1.0)
            attention_weights: List of attention weights for sequential steps
        """
        if not feature_vectors:
            # Cold start baseline
            return "LEGITIMATE USER", 0.88, [1.0]

        # Convert feature dicts to numpy matrix
        raw_matrix = np.array(
            [[f.get(k, 0.0) for k in self.feature_names] for f in feature_vectors],
            dtype=np.float32
        )

        # Preprocess
        norm_matrix = self.preprocessor.transform(raw_matrix) if self.preprocessor else raw_matrix

        # Shape: (1, seq_len, input_dim)
        input_tensor = torch.tensor(norm_matrix, dtype=torch.float32).unsqueeze(0).to(self.device)

        confidence, attn_weights = self.model.predict_probability(input_tensor)
        confidence = float(np.clip(confidence, 0.01, 0.99))

        # Decision thresholding
        if confidence >= settings.CONFIDENCE_THRESHOLD_LEGITIMATE:
            classification = "LEGITIMATE USER"
        elif confidence >= settings.CONFIDENCE_THRESHOLD_SUSPICIOUS:
            classification = "SUSPICIOUS USER"
        else:
            classification = "POTENTIAL INTRUDER"

        if attn_weights is None:
            attn_weights = [1.0 / len(feature_vectors)] * len(feature_vectors)

        return classification, round(confidence, 4), attn_weights


model_service = ModelService()
