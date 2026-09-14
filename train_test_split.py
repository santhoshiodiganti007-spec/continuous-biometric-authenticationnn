import pandas as pd
import numpy as np
import os

# ==============================
# SETTINGS
# ==============================

INPUT_FILE = "processed_data/all_users_processed.csv"
OUTPUT_FOLDER = "splits"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ==============================
# LOAD DATA
# ==============================

print("=" * 60)
print("CREATING TRAIN / TEST SPLIT")
print("=" * 60)

data = pd.read_csv(INPUT_FILE)

print("\nTotal events:", len(data))

# ==============================
# GET SESSIONS
# ==============================

sessions = data["session"].unique()

print("\nTotal sessions:", len(sessions))

for session in sessions:
    session_data = data[data["session"] == session]
    label = session_data["label"].iloc[0]

    print(
        session,
        "-> label:",
        int(label),
        "events:",
        len(session_data)
    )

# ==============================
# MANUAL SESSION SPLIT
# ==============================

# User 1 sessions
user1_sessions = [
    session for session in sessions
    if data[data["session"] == session]["label"].iloc[0] == 1
]

# User 2 sessions
user2_sessions = [
    session for session in sessions
    if data[data["session"] == session]["label"].iloc[0] == 0
]

print("\nUser 1 sessions:", len(user1_sessions))
print("User 2 sessions:", len(user2_sessions))

# Use approximately 2/3 sessions for training
# and 1/3 sessions for testing

train_user1 = user1_sessions[:2]
test_user1 = user1_sessions[2:]

train_user2 = user2_sessions[:3]
test_user2 = user2_sessions[3:]

train_sessions = train_user1 + train_user2
test_sessions = test_user1 + test_user2

# ==============================
# CREATE DATASETS
# ==============================

train_data = data[
    data["session"].isin(train_sessions)
]

test_data = data[
    data["session"].isin(test_sessions)
]

# ==============================
# DISPLAY RESULTS
# ==============================

print("\n" + "=" * 60)
print("SPLIT COMPLETED")
print("=" * 60)

print("\nTraining sessions:")
for session in train_sessions:
    print(" -", session)

print("\nTesting sessions:")
for session in test_sessions:
    print(" -", session)

print("\nTraining events:", len(train_data))
print("Testing events:", len(test_data))

print("\nTraining label distribution:")
print(train_data["label"].value_counts())

print("\nTesting label distribution:")
print(test_data["label"].value_counts())

# ==============================
# SAVE
# ==============================

train_file = os.path.join(
    OUTPUT_FOLDER,
    "train_data.csv"
)

test_file = os.path.join(
    OUTPUT_FOLDER,
    "test_data.csv"
)

train_data.to_csv(
    train_file,
    index=False
)

test_data.to_csv(
    test_file,
    index=False
)

print("\nSaved:")
print(train_file)
print(test_file)

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)