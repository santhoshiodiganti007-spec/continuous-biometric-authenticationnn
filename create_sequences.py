import pandas as pd
import numpy as np
import os

# ==============================
# SETTINGS
# ==============================

INPUT_FILE = "processed_data/all_users_processed.csv"
OUTPUT_FOLDER = "sequences"

WINDOW_SIZE = 50
STEP_SIZE = 25

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ==============================
# FEATURES
# ==============================

FEATURES = [
    "x",
    "y",
    "dx",
    "dy",
    "distance",
    "velocity",
    "hold_time",
    "flight_time"
]

# ==============================
# LOAD DATA
# ==============================

print("=" * 60)
print("CREATING BEHAVIORAL SEQUENCES")
print("=" * 60)

print("\nLoading:", INPUT_FILE)

data = pd.read_csv(INPUT_FILE)

print("Total events:", len(data))

# ==============================
# CREATE SEQUENCES
# ==============================

all_sequences = []
all_labels = []

# Process each session separately
for session_name, session_data in data.groupby("session"):

    print("\nProcessing session:")
    print(session_name)

    values = session_data[FEATURES].values

    # Get the label of this session
    label = session_data["label"].iloc[0]

    print("User label:", label)
    print("Events:", len(values))

    # Sliding window
    for start in range(
        0,
        len(values) - WINDOW_SIZE + 1,
        STEP_SIZE
    ):

        end = start + WINDOW_SIZE

        window = values[start:end]

        all_sequences.append(window)

        all_labels.append(label)

# ==============================
# CONVERT TO NUMPY
# ==============================

X = np.array(
    all_sequences,
    dtype=np.float32
)

y = np.array(
    all_labels,
    dtype=np.float32
)

# ==============================
# DISPLAY SHAPES
# ==============================

print("\n" + "=" * 60)
print("SEQUENCE CREATION COMPLETED")
print("=" * 60)

print("\nX shape:")
print(X.shape)

print("\ny shape:")
print(y.shape)

# ==============================
# LABEL DISTRIBUTION
# ==============================

print("\nSequence label distribution:")

unique, counts = np.unique(
    y,
    return_counts=True
)

for label, count in zip(unique, counts):

    print(
        "Label",
        int(label),
        ":",
        count,
        "sequences"
    )

# ==============================
# SAVE
# ==============================

X_file = os.path.join(
    OUTPUT_FOLDER,
    "X_all_users.npy"
)

y_file = os.path.join(
    OUTPUT_FOLDER,
    "y_all_users.npy"
)

np.save(X_file, X)
np.save(y_file, y)

# ==============================
# FINAL INFORMATION
# ==============================

print("\nSaved files:")

print(X_file)
print(y_file)

print("\nEach sequence contains:")
print(WINDOW_SIZE, "behavioral events")

print("\nEach event contains:")
print(len(FEATURES), "features")

print("\nFeatures:")

for feature in FEATURES:
    print(" -", feature)

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)