"""Explainable PyTorch Transformer model for continuous behavioral biometric authentication."""

import math
from typing import Tuple, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for sequential behavioral feature vectors."""

    def __init__(self, d_model: int, max_len: int = 500, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # Shape: (1, max_len, d_model)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x shape: (batch_size, seq_len, d_model)
        """
        seq_len = x.size(1)
        x = x + self.pe[:, :seq_len, :]
        return self.dropout(x)


class BehavioralTransformer(nn.Module):
    """
    Continuous Biometric Authentication Transformer with explainable self-attention extraction.
    Classifies behavioral feature sequences into legitimate (1) vs intruder (0).
    """

    def __init__(
        self,
        input_dim: int = 16,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        dropout: float = 0.1,
        max_seq_len: int = 100
    ):
        super().__init__()
        self.input_dim = input_dim
        self.d_model = d_model

        # 1. Feature Embedding Projection
        self.embedding = nn.Sequential(
            nn.Linear(input_dim, d_model),
            nn.LayerNorm(d_model),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        # 2. Positional Encoding
        self.pos_encoder = PositionalEncoding(d_model=d_model, max_len=max_seq_len, dropout=dropout)

        # 3. Custom Transformer Encoder Layers with attention weight exposure
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            activation="relu"
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # 4. Self-attention pooling layer
        self.attention_pool = nn.Sequential(
            nn.Linear(d_model, 1),
            nn.Softmax(dim=1)
        )

        # 5. Classification Head
        self.classifier = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)  # Binary logit (Legitimate vs Impostor)
        )

    def forward(
        self,
        x: torch.Tensor,
        return_attention: bool = False
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Args:
            x: Input tensor of shape (batch_size, seq_len, input_dim)
            return_attention: Whether to return sequence attention weights
        Returns:
            logits: (batch_size, 1)
            attention_weights: (batch_size, seq_len) if return_attention else None
        """
        # Feature embedding projection
        embedded = self.embedding(x)  # (batch_size, seq_len, d_model)

        # Positional encoding
        encoded = self.pos_encoder(embedded)

        # Transformer representation
        transformer_out = self.transformer_encoder(encoded)  # (batch_size, seq_len, d_model)

        # Sequence Attention Pooling
        attn_weights = self.attention_pool(transformer_out)  # (batch_size, seq_len, 1)
        pooled = torch.sum(transformer_out * attn_weights, dim=1)  # (batch_size, d_model)

        # Classification Logits
        logits = self.classifier(pooled)  # (batch_size, 1)

        if return_attention:
            return logits, attn_weights.squeeze(-1)
        return logits, None

    def predict_probability(self, x: torch.Tensor) -> Tuple[float, Optional[list]]:
        """Inference helper returning legitimate probability in range [0.0, 1.0]."""
        self.eval()
        with torch.no_grad():
            logits, attn = self.forward(x, return_attention=True)
            probs = torch.sigmoid(logits).cpu().numpy().flatten()
            attn_list = attn[0].tolist() if attn is not None else None
            return float(probs[0]), attn_list
