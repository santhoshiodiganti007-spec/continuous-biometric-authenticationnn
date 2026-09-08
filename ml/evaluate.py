"""Biometric evaluation suite computing FAR, FRR, EER, ROC-AUC, and generating plots."""

import os
import sys
import json
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_curve,
    roc_auc_score,
    confusion_matrix
)

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.models.transformer import BehavioralTransformer


def compute_eer(y_true, y_scores):
    """
    Computes False Acceptance Rate (FAR), False Rejection Rate (FRR),
    and Equal Error Rate (EER) across varying decision thresholds.
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    fnr = 1.0 - tpr  # False Rejection Rate (FRR)
    far = fpr        # False Acceptance Rate (FAR)

    # Find the threshold where FAR and FRR intersect
    eer_index = np.nanargmin(np.abs(far - fnr))
    eer = (far[eer_index] + fnr[eer_index]) / 2.0
    eer_threshold = thresholds[eer_index]

    return float(eer), float(eer_threshold), far, fnr, thresholds


def evaluate_biometric_transformer(
    model_path="ml/saved_models/best_transformer.pt",
    test_data_path="ml/saved_models/test_data.npz",
    output_dir="ml/saved_models"
):
    """Evaluates trained Transformer on unseen test sessions and computes biometric metrics."""
    if not os.path.exists(model_path) or not os.path.exists(test_data_path):
        print(f"Error: Model ({model_path}) or test data ({test_data_path}) missing. Please run train.py first.")
        return

    # Load test data
    data = np.load(test_data_path)
    X_test = data["X_test"]
    y_test = data["y_test"]

    # Load checkpoint
    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
    input_dim = checkpoint.get("input_dim", X_test.shape[1])
    d_model = checkpoint.get("d_model", 64)
    nhead = checkpoint.get("nhead", 4)
    num_layers = checkpoint.get("num_layers", 2)

    model = BehavioralTransformer(
        input_dim=input_dim,
        d_model=d_model,
        nhead=nhead,
        num_layers=num_layers
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Inference
    with torch.no_grad():
        test_tensor = torch.tensor(X_test, dtype=torch.float32).unsqueeze(1)
        logits, _ = model(test_tensor)
        probs = torch.sigmoid(logits).cpu().numpy().flatten()

    binary_preds = (probs >= 0.5).astype(int)

    # Standard metrics
    acc = float(accuracy_score(y_test, binary_preds))
    prec = float(precision_score(y_test, binary_preds, zero_division=0))
    rec = float(recall_score(y_test, binary_preds, zero_division=0))
    f1 = float(f1_score(y_test, binary_preds, zero_division=0))
    auc = float(roc_auc_score(y_test, probs))

    # Biometric metrics: FAR, FRR, EER
    eer, eer_thresh, far, frr, thresholds = compute_eer(y_test, probs)

    # Confusion matrix
    cm = confusion_matrix(y_test, binary_preds).tolist()

    report = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "equal_error_rate_eer": round(eer, 4),
        "eer_threshold": round(eer_thresh, 4),
        "confusion_matrix": cm,
        "sample_counts": {
            "total": len(y_test),
            "legitimate": int(np.sum(y_test == 1)),
            "impostor": int(np.sum(y_test == 0))
        }
    }

    # Save metrics JSON
    json_path = os.path.join(output_dir, "evaluation_report.json")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=4)

    # Generate and save plots
    # 1. ROC Curve
    plt.figure(figsize=(6, 5))
    plt.plot(far, 1.0 - frr, color="#06b6d4", lw=2, label=f"Transformer ROC (AUC = {auc:.3f})")
    plt.plot([0, 1], [0, 1], color="#64748b", linestyle="--")
    plt.xlabel("False Acceptance Rate (FAR)")
    plt.ylabel("True Acceptance Rate (TAR / 1 - FRR)")
    plt.title("Biometric ROC Curve")
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "roc_curve.png"), dpi=200)
    plt.close()

    # 2. FAR vs FRR / EER Curve
    plt.figure(figsize=(6, 5))
    valid_thresh_idx = (thresholds >= 0.0) & (thresholds <= 1.0)
    plt.plot(thresholds[valid_thresh_idx], far[valid_thresh_idx], color="#f43f5e", lw=2, label="FAR")
    plt.plot(thresholds[valid_thresh_idx], frr[valid_thresh_idx], color="#3b82f6", lw=2, label="FRR")
    plt.scatter([eer_thresh], [eer], color="#10b981", s=80, zorder=5, label=f"EER = {eer:.2%}")
    plt.xlabel("Decision Threshold")
    plt.ylabel("Error Rate")
    plt.title("FAR vs. FRR Biometric Tradeoff")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "eer_plot.png"), dpi=200)
    plt.close()

    print("\n================ BIOMETRIC EVALUATION REPORT ================")
    print(f"Accuracy:  {acc:.2%}")
    print(f"Precision: {prec:.2%}")
    print(f"Recall:    {rec:.2%}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC-AUC:   {auc:.4f}")
    print(f"EER:       {eer:.2%} (Threshold = {eer_thresh:.3f})")
    print(f"Metrics saved to {json_path}")
    print("============================================================\n")


if __name__ == "__main__":
    evaluate_biometric_transformer()
