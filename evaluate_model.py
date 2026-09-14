import numpy as np
import torch
import torch.nn as nn

from torch.utils.data import DataLoader, TensorDataset

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_curve,
    auc
)


# ============================================================
# SETTINGS
# ============================================================

X_FILE = "sequences/X_all_users.npy"
Y_FILE = "sequences/y_all_users.npy"
USER_FILE = "sequences/user_ids_all_users.npy"
SESSION_FILE = "sequences/sessions_all_users.npy"

BATCH_SIZE = 32
EPOCHS = 20
LEARNING_RATE = 0.001

INPUT_SIZE = 8
SEQUENCE_LENGTH = 50

D_MODEL = 64
NUM_HEADS = 4
NUM_LAYERS = 2
DROPOUT = 0.1


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("SESSION-BASED CONTINUOUS AUTHENTICATION")
print("=" * 70)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading sequence data...")

X = np.load(X_FILE)
y = np.load(Y_FILE)
user_ids = np.load(USER_FILE)
sessions = np.load(SESSION_FILE)

print("\nX shape:", X.shape)
print("y shape:", y.shape)
print("User IDs shape:", user_ids.shape)
print("Sessions shape:", sessions.shape)


# ============================================================
# FIND SESSIONS FOR EACH USER
# ============================================================

print("\n" + "=" * 70)
print("SESSION INFORMATION")
print("=" * 70)

unique_users = np.unique(user_ids)

train_indices = []
test_indices = []

for user in unique_users:

    user_mask = user_ids == user

    user_sessions = np.unique(
        sessions[user_mask]
    )

    user_sessions = sorted(
        user_sessions.astype(str)
    )

    print("\nUser:", user)

    for i, session in enumerate(user_sessions):

        session_mask = (
            (user_ids == user) &
            (sessions.astype(str) == session)
        )

        indices = np.where(session_mask)[0]

        print(
            f"Session {i + 1}: "
            f"{session} -> "
            f"{len(indices)} sequences"
        )

        # First two sessions = training
        if i < 2:
            train_indices.extend(indices)

        # Third session = testing
        else:
            test_indices.extend(indices)


# ============================================================
# CREATE TRAIN / TEST DATA
# ============================================================

train_indices = np.array(train_indices)
test_indices = np.array(test_indices)

X_train = X[train_indices]
y_train = y[train_indices]

X_test = X[test_indices]
y_test = y[test_indices]


print("\n" + "=" * 70)
print("DATA SPLIT")
print("=" * 70)

print("\nTraining sequences:", len(X_train))
print("Testing sequences:", len(X_test))

print("\nTraining labels:")
print("User 1:", np.sum(y_train == 1))
print("Other:", np.sum(y_train == 0))

print("\nTesting labels:")
print("User 1:", np.sum(y_test == 1))
print("Other:", np.sum(y_test == 0))


# ============================================================
# CONVERT TO PYTORCH
# ============================================================

X_train = torch.tensor(
    X_train,
    dtype=torch.float32
)

X_test = torch.tensor(
    X_test,
    dtype=torch.float32
)

y_train = torch.tensor(
    y_train,
    dtype=torch.float32
)

y_test = torch.tensor(
    y_test,
    dtype=torch.float32
)


train_dataset = TensorDataset(
    X_train,
    y_train
)

test_dataset = TensorDataset(
    X_test,
    y_test
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

        # Convert 8 behavioral features into 64 dimensions
        self.input_projection = nn.Linear(
            INPUT_SIZE,
            D_MODEL
        )

        # Learn position information
        self.position_embedding = nn.Parameter(
            torch.randn(
                1,
                SEQUENCE_LENGTH,
                D_MODEL
            )
        )

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=D_MODEL,
            nhead=NUM_HEADS,
            dropout=DROPOUT,
            batch_first=True
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=NUM_LAYERS
        )

        # Final classification layer
        self.classifier = nn.Linear(
            D_MODEL,
            1
        )


    def forward(self, x):

        x = self.input_projection(x)

        x = x + self.position_embedding

        x = self.transformer(x)

        # Average all 50 events
        x = x.mean(dim=1)

        x = self.classifier(x)

        return x.squeeze(1)


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print("\nUsing device:", device)


# ============================================================
# CREATE MODEL
# ============================================================

model = ContinuousAuthenticationTransformer().to(device)


criterion = nn.BCEWithLogitsLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)


# ============================================================
# TRAINING
# ============================================================

print("\n" + "=" * 70)
print("STARTING SESSION-BASED TRAINING")
print("=" * 70)


for epoch in range(EPOCHS):

    model.train()

    total_loss = 0

    for batch_X, batch_y in train_loader:

        batch_X = batch_X.to(device)
        batch_y = batch_y.to(device)

        optimizer.zero_grad()

        outputs = model(batch_X)

        loss = criterion(
            outputs,
            batch_y
        )

        loss.backward()

        optimizer.step()

        total_loss += loss.item()


    average_loss = (
        total_loss /
        len(train_loader)
    )

    print(
        f"Epoch [{epoch + 1}/{EPOCHS}] "
        f"Loss: {average_loss:.4f}"
    )


# ============================================================
# TEST MODEL
# ============================================================

print("\n" + "=" * 70)
print("TESTING ON UNSEEN SESSION")
print("=" * 70)


model.eval()

all_probabilities = []
all_actual = []


with torch.no_grad():

    for batch_X, batch_y in test_loader:

        batch_X = batch_X.to(device)

        outputs = model(batch_X)

        probabilities = torch.sigmoid(
            outputs
        )

        all_probabilities.extend(
            probabilities.cpu().numpy()
        )

        all_actual.extend(
            batch_y.numpy()
        )


all_probabilities = np.array(
    all_probabilities
)

all_actual = np.array(
    all_actual
)


# ============================================================
# THRESHOLD = 0.5
# ============================================================

threshold = 0.5

all_predictions = (
    all_probabilities >= threshold
).astype(int)


# ============================================================
# BASIC METRICS
# ============================================================

accuracy = accuracy_score(
    all_actual,
    all_predictions
)

precision = precision_score(
    all_actual,
    all_predictions,
    zero_division=0
)

recall = recall_score(
    all_actual,
    all_predictions,
    zero_division=0
)

f1 = f1_score(
    all_actual,
    all_predictions,
    zero_division=0
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    all_actual,
    all_predictions
)

TN, FP, FN, TP = cm.ravel()


# ============================================================
# FAR AND FRR
# ============================================================

FAR = FP / (FP + TN) if (FP + TN) > 0 else 0

FRR = FN / (FN + TP) if (FN + TP) > 0 else 0


# ============================================================
# ROC / AUC
# ============================================================

fpr, tpr, thresholds = roc_curve(
    all_actual,
    all_probabilities
)

roc_auc = auc(
    fpr,
    tpr
)


# ============================================================
# EER
# ============================================================

fnr = 1 - tpr

eer_index = np.nanargmin(
    np.abs(fpr - fnr)
)

EER = (
    fpr[eer_index] +
    fnr[eer_index]
) / 2


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n" + "=" * 70)
print("FINAL RESEARCH METRICS")
print("=" * 70)

print(
    f"\nAccuracy : {accuracy * 100:.2f}%"
)

print(
    f"Precision: {precision * 100:.2f}%"
)

print(
    f"Recall   : {recall * 100:.2f}%"
)

print(
    f"F1 Score : {f1 * 100:.2f}%"
)

print(
    f"FAR      : {FAR * 100:.2f}%"
)

print(
    f"FRR      : {FRR * 100:.2f}%"
)

print(
    f"EER      : {EER * 100:.2f}%"
)

print(
    f"ROC-AUC  : {roc_auc:.4f}"
)


print("\nConfusion Matrix:")

print(cm)


# ============================================================
# SAVE MODEL
# ============================================================

MODEL_FILE = (
    "transformer_session_based.pth"
)

torch.save(
    model.state_dict(),
    MODEL_FILE
)


print("\n" + "=" * 70)
print("MODEL SAVED")
print("=" * 70)

print(
    "\nSaved as:",
    MODEL_FILE
)

print("\nDONE!")