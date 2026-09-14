"""Training pipeline for continuous biometric authentication Transformer model."""

import os
import sys
import argparse
import logging
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.models.transformer import BehavioralTransformer
from app.services.feature_engineering import BehavioralFeatureExtractor
from ml.dataset_builder import BehavioralDatasetBuilder
from ml.preprocess import prepare_and_normalize_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("train_transformer")


def train_behavioral_transformer(
    epochs: int = 20,
    batch_size: int = 32,
    lr: float = 0.001,
    d_model: int = 64,
    nhead: int = 4,
    num_layers: int = 2,
    save_path: str = "ml/saved_models/best_transformer.pt"
):
    """Executes dataset synthesis/extraction, normalization, training, and early stopping checkpointing."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # 1. Build Research Dataset (Benchmark with session isolation)
    logger.info("Building session-isolated behavioral dataset...")
    X_train, y_train, X_val, y_val, X_test, y_test = BehavioralDatasetBuilder.generate_synthetic_research_benchmark()

    # 2. Normalize using train-only fitted scaler
    logger.info("Normalizing feature distributions...")
    X_train_norm, X_val_norm, X_test_norm, scaler = prepare_and_normalize_data(X_train, X_val, X_test)

    # Convert to PyTorch Tensors (reshape as sequence: batch_size, seq_len=1, input_dim)
    input_dim = X_train_norm.shape[1]

    train_dataset = TensorDataset(
        torch.tensor(X_train_norm, dtype=torch.float32).unsqueeze(1),
        torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    )
    val_dataset = TensorDataset(
        torch.tensor(X_val_norm, dtype=torch.float32).unsqueeze(1),
        torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)
    )
    test_dataset = TensorDataset(
        torch.tensor(X_test_norm, dtype=torch.float32).unsqueeze(1),
        torch.tensor(y_test, dtype=torch.float32).unsqueeze(1)
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # 3. Instantiate Transformer Model
    model = BehavioralTransformer(
        input_dim=input_dim,
        d_model=d_model,
        nhead=nhead,
        num_layers=num_layers,
        dim_feedforward=128,
        dropout=0.1
    ).to(device)

    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    best_val_loss = float("inf")
    best_val_f1 = 0.0
    patience = 5
    patience_counter = 0

    logger.info(f"Beginning Transformer training for {epochs} epochs...")

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            logits, _ = model(batch_x)
            loss = criterion(logits, batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item() * batch_x.size(0)

        train_loss /= len(train_loader.dataset)

        # Validation phase
        model.eval()
        val_loss = 0.0
        val_preds = []
        val_targets = []
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                logits, _ = model(batch_x)
                loss = criterion(logits, batch_y)
                val_loss += loss.item() * batch_x.size(0)
                probs = torch.sigmoid(logits).cpu().numpy()
                val_preds.extend(probs)
                val_targets.extend(batch_y.cpu().numpy())

        val_loss /= len(val_loader.dataset)
        val_preds = np.array(val_preds).flatten()
        val_targets = np.array(val_targets).flatten()
        val_binary = (val_preds >= 0.5).astype(int)

        val_acc = accuracy_score(val_targets, val_binary)
        val_f1 = f1_score(val_targets, val_binary, zero_division=0)
        val_auc = roc_auc_score(val_targets, val_preds)

        logger.info(
            f"Epoch {epoch:02d}/{epochs} | "
            f"Train Loss: {train_loss:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Val Acc: {val_acc:.4f} | "
            f"Val F1: {val_f1:.4f} | "
            f"Val ROC-AUC: {val_auc:.4f}"
        )

        # Checkpointing
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_val_f1 = val_f1
            patience_counter = 0

            torch.save({
                "model_state_dict": model.state_dict(),
                "input_dim": input_dim,
                "d_model": d_model,
                "nhead": nhead,
                "num_layers": num_layers,
                "scaler_means": scaler.means,
                "scaler_stds": scaler.stds,
                "val_acc": val_acc,
                "val_f1": val_f1,
                "val_auc": val_auc
            }, save_path)
            logger.info(f"--> Saved best model checkpoint to {save_path}")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping triggered at epoch {epoch}.")
                break

    # Save test dataset for offline evaluation
    np.savez_compressed(
        "ml/saved_models/test_data.npz",
        X_test=X_test_norm,
        y_test=y_test
    )
    logger.info("Training complete. Test data saved to ml/saved_models/test_data.npz.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    args = parser.parse_args()

    train_behavioral_transformer(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr
    )
