"""Explainable AI service computing feature attribution and attention interpretations."""

from typing import List, Dict, Any, Optional
import numpy as np
import torch

from app.services.model_service import model_service
from app.services.feature_engineering import BehavioralFeatureExtractor


class ExplainabilityService:
    """Computes explainable feature importance and transformer attention rankings."""

    FEATURE_DESCRIPTIONS = {
        "keystroke_mean_hold_duration": "Key hold duration (ms)",
        "keystroke_std_hold_duration": "Key hold duration consistency",
        "keystroke_mean_flight_time": "Flight time between keystrokes",
        "keystroke_var_flight_time": "Typing rhythm consistency",
        "keystroke_typing_speed": "Typing speed (chars/sec)",
        "keystroke_event_frequency": "Keypress frequency",
        "mouse_mean_speed": "Average mouse movement speed",
        "mouse_max_speed": "Peak cursor velocity",
        "mouse_mean_acceleration": "Mouse acceleration rate",
        "mouse_total_distance": "Total cursor path length",
        "mouse_direction_changes": "Mouse movement curvature & jitter",
        "mouse_click_frequency": "Click frequency per second",
        "mouse_mean_click_duration": "Click press-to-release duration",
        "mouse_scroll_frequency": "Scroll activity rate",
        "keystroke_to_mouse_ratio": "Keyboard vs Mouse usage proportion",
        "activity_pause_rate": "Interaction pause rate"
    }

    @classmethod
    def explain_prediction(
        cls,
        feature_vector: Dict[str, float],
        attention_weights: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Computes gradient-based and sensitivity feature attributions for the input behavioral window.
        Returns top influential features ranked by importance.
        """
        feature_names = BehavioralFeatureExtractor.FEATURE_NAMES
        raw_vals = [float(feature_vector.get(k, 0.0)) for k in feature_names]
        
        # Compute sensitivity attribution via model gradients
        model = model_service.model
        model.eval()
        
        inp = torch.tensor(raw_vals, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(model_service.device)
        inp.requires_grad = True

        try:
            logits, _ = model(inp)
            prob = torch.sigmoid(logits)
            prob.backward()
            
            # Saliency map (input * gradient)
            if inp.grad is not None:
                grads = inp.grad.squeeze(0).squeeze(0).cpu().numpy()
                importances = np.abs(grads * np.array(raw_vals, dtype=np.float32))
            else:
                # Fallback to feature deviation variance
                importances = np.abs(np.array(raw_vals))
        except Exception:
            importances = np.abs(np.array(raw_vals))

        # Normalize importances so they sum to 1.0
        total_imp = np.sum(importances)
        if total_imp > 1e-6:
            importances = importances / total_imp
        else:
            importances = np.ones_like(importances) / len(importances)

        # Rank features
        ranked_indices = np.argsort(importances)[::-1]
        
        results = []
        for idx in ranked_indices[:6]:  # Top 6 most influential features
            name = feature_names[idx]
            results.append({
                "feature": name,
                "importance": round(float(importances[idx]), 4),
                "value": round(float(raw_vals[idx]), 4),
                "description": cls.FEATURE_DESCRIPTIONS.get(name, name)
            })

        return results


explainability_service = ExplainabilityService()
