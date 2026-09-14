import pandas as pd
import numpy as np
import os

# ==============================
# SETTINGS
# ==============================

WINDOW_SIZE = 50
STEP_SIZE = 25

OUTPUT_FOLDER = "sequences"

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
# FUNCTION TO CREATE SEQUENCES
# ==============================

def create_sequences(input_file, output_prefix):

    print("\n" + "=" * 60)
    print("PROCESSING:", input_file)
    print("=" * 60)

    data = pd.read_csv(input_file)

    print("Total events:", len(data))

    all_sequences = []
    all_labels = []

    # Process each session separately
    for session_name, session_data in data.groupby("session"):

        print("\nSession:", session_name)

        values = session_data[FEATURES].values

        label = session_data["label"].iloc[0]

        print("Label:", int(label))
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

    # Convert to NumPy
    X = np.array(
        all_sequences,
        dtype=np.float32
    )

    y = np.array(
        all_labels,
        dtype=np.float32
    )

    print("\nSequences created:", len(X))
    print("X shape:", X.shape)
    print("y shape:", y.shape)

    # Label distribution
    unique, counts = np.unique(
        y,
        return_counts=True
    )

    print("\nLabel distribution:")

    for label, count in zip(unique, counts):

        print(
            "Label",
            int(label),
            ":",
            count
        )

    # Save
    X_file = os.path.join(
        OUTPUT_FOLDER,
        "X_" + output_prefix + ".npy"
    )

    y_file = os.path.join(
        OUTPUT_FOLDER,
        "y_" + output_prefix + ".npy"
    )

    np.save(X_file, X)
    np.save(y_file, y)

    print("\nSaved:")
    print(X_file)
    print(y_file)

    return X, y


# ==============================
# TRAINING SEQUENCES
# ==============================

X_train, y_train = create_sequences(
    "splits/train_data.csv",
    "train"
)


# ==============================
# TESTING SEQUENCES
# ==============================

X_test, y_test = create_sequences(
    "splits/test_data.csv",
    "test"
)


# ==============================
# FINAL SUMMARY
# ==============================

print("\n" + "=" * 60)
print("TRAIN / TEST SEQUENCES COMPLETED")
print("=" * 60)

print("\nTraining:")
print("X_train:", X_train.shape)
print("y_train:", y_train.shape)

print("\nTesting:")
print("X_test:", X_test.shape)
print("y_test:", y_test.shape)

print("\nEach sequence:")
print(WINDOW_SIZE, "events ×", len(FEATURES), "features")

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)