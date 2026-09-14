import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# ============================================================
# SETTINGS
# ============================================================

EPOCHS = 30
BATCH_SIZE = 32
LEARNING_RATE = 0.001

# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 60)
print("TRANSFORMER CONTINUOUS AUTHENTICATION")
print("=" * 60)

print("\nDevice:", device)

# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading training data...")

X_train = np.load("sequences/X_train.npy")
y_train = np.load("sequences/y_train.npy")

print("X_train:", X_train.shape)
print("y_train:", y_train.shape)

print("\nLoading testing data...")

X_test = np.load("sequences/X_test.npy")
y_test = np.load("sequences/y_test.npy")

print("X_test:", X_test.shape)
print("y_test:", y_test.shape)

# ============================================================
# NORMALIZATION
# ============================================================

print("\nNormalizing features...")

# Fit scaler ONLY on training data
scaler = StandardScaler()

X_train_2d = X_train.reshape(-1, X_train.shape[-1])

X_test_2d = X_test.reshape(-1, X_test.shape[-1])

scaler.fit(X_train_2d)

X_train_2d = scaler.transform(X_train_2d)
X_test_2d = scaler.transform(X_test_2d)

X_train = X_train_2d.reshape(
    X_train.shape
)

X_test = X_test_2d.reshape(
    X_test.shape
)

print("Normalization completed.")

# ============================================================
# CONVERT TO PYTORCH TENSORS
# ============================================================

X_train_tensor = torch.tensor(
    X_train,
    dtype=torch.float32
)

y_train_tensor = torch.tensor(
    y_train,
    dtype=torch.float32
)

X_test_tensor = torch.tensor(
    X_test,
    dtype=torch.float32
)

y_test_tensor = torch.tensor(
    y_test,
    dtype=torch.float32
)

# ============================================================
# DATA LOADERS
# ============================================================

train_dataset = TensorDataset(
    X_train_tensor,
    y_train_tensor
)

test_dataset = TensorDataset(
    X_test_tensor,
    y_test_tensor
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)

# ============================================================
# TRANSFORMER MODEL
# ============================================================

class ContinuousAuthenticationTransformer(nn.Module):

    def __init__(self):

        super().__init__()

        # Input features = 8
        self.input_projection = nn.Linear(
            8,
            64
        )

        # Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=64,
            nhead=4,
            dim_feedforward=128,
            dropout=0.1,
            batch_first=True
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=2
        )

        # Classification layers
        self.classifier = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1)
        )

    def forward(self, x):

        # Convert 8 features → 64 dimensions
        x = self.input_projection(x)

        # Transformer
        x = self.transformer(x)

        # Average all 50 time steps
        x = x.mean(dim=1)

        # Classification
        x = self.classifier(x)

        return x.squeeze(1)


# ============================================================
# CREATE MODEL
# ============================================================

model = ContinuousAuthenticationTransformer()

model = model.to(device)

print("\nModel:")
print(model)

# ============================================================
# LOSS AND OPTIMIZER
# ============================================================

criterion = nn.BCEWithLogitsLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)

# ============================================================
# TRAINING
# ============================================================

print("\n" + "=" * 60)
print("STARTING TRAINING")
print("=" * 60)

for epoch in range(EPOCHS):

    model.train()

    total_loss = 0

    for X_batch, y_batch in train_loader:

        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)

        # Forward pass
        outputs = model(X_batch)

        # Calculate loss
        loss = criterion(
            outputs,
            y_batch
        )

        # Clear gradients
        optimizer.zero_grad()

        # Backpropagation
        loss.backward()

        # Update weights
        optimizer.step()

        total_loss += loss.item()

    average_loss = (
        total_loss /
        len(train_loader)
    )

    # ========================================================
    # TESTING AFTER EACH EPOCH
    # ========================================================

    model.eval()

    predictions = []
    actual = []

    with torch.no_grad():

        for X_batch, y_batch in test_loader:

            X_batch = X_batch.to(device)

            outputs = model(X_batch)

            probabilities = torch.sigmoid(
                outputs
            )

            preds = (
                probabilities >= 0.5
            ).int()

            predictions.extend(
                preds.cpu().numpy()
            )

            actual.extend(
                y_batch.numpy()
            )

    accuracy = accuracy_score(
        actual,
        predictions
    )

    print(
        f"Epoch [{epoch + 1:02d}/{EPOCHS}] "
        f"Loss: {average_loss:.4f} "
        f"Test Accuracy: {accuracy:.4f}"
    )

# ============================================================
# FINAL EVALUATION
# ============================================================

print("\n" + "=" * 60)
print("FINAL MODEL EVALUATION")
print("=" * 60)

accuracy = accuracy_score(
    actual,
    predictions
)

precision = precision_score(
    actual,
    predictions,
    zero_division=0
)

recall = recall_score(
    actual,
    predictions,
    zero_division=0
)

f1 = f1_score(
    actual,
    predictions,
    zero_division=0
)

print("\nAccuracy :", round(accuracy, 4))
print("Precision:", round(precision, 4))
print("Recall   :", round(recall, 4))
print("F1 Score :", round(f1, 4))

# ============================================================
# SAVE MODEL
# ============================================================

torch.save(
    model.state_dict(),
    "transformer_authentication_model.pth"
)

print("\nModel saved as:")
print("transformer_authentication_model.pth")

print("\n" + "=" * 60)
print("TRAINING COMPLETED")
print("=" * 60)