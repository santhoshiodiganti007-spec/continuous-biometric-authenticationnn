import pandas as pd
import os
import glob

# ==============================
# SETTINGS
# ==============================

DATASET_FOLDER = "dataset"
OUTPUT_FOLDER = "processed_data"

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
# FIND CSV FILES
# ==============================

csv_files = glob.glob(
    os.path.join(DATASET_FOLDER, "user_*", "*.csv")
)

print("=" * 60)
print("MULTI-USER DATA PREPROCESSING")
print("=" * 60)

print("\nCSV files found:", len(csv_files))

all_data = []

# ==============================
# PROCESS EACH CSV
# ==============================

for file in csv_files:

    print("\nReading:", file)

    data = pd.read_csv(file)

    print("Rows:", len(data))

    # Get user folder
    user_folder = os.path.basename(
        os.path.dirname(file)
    )

    # user_001 -> 1
    user_id = int(
        user_folder.replace("user_", "")
    )

    # Get session filename
    session_name = os.path.basename(file)

    # ==============================
    # LABEL
    # ==============================

    if user_id == 1:
        label = 1
    else:
        label = 0

    data["user_id"] = user_id
    data["label"] = label
    data["session"] = session_name

    all_data.append(data)

# ==============================
# CHECK DATA
# ==============================

if len(all_data) == 0:

    print("\nERROR: No CSV files found!")

    exit()

# ==============================
# COMBINE
# ==============================

combined_data = pd.concat(
    all_data,
    ignore_index=True
)

print("\n" + "=" * 60)
print("ALL DATA COMBINED")
print("=" * 60)

print("\nTotal rows:", len(combined_data))

# ==============================
# KEEP REQUIRED COLUMNS
# ==============================

combined_data = combined_data[
    FEATURES + [
        "user_id",
        "label",
        "session"
    ]
]

# ==============================
# CONVERT FEATURES TO NUMBERS
# ==============================

combined_data[FEATURES] = combined_data[
    FEATURES
].apply(
    pd.to_numeric,
    errors="coerce"
)

# Replace missing values with 0
combined_data[FEATURES] = combined_data[
    FEATURES
].fillna(0)

# ==============================
# SAVE
# ==============================

output_file = os.path.join(
    OUTPUT_FOLDER,
    "all_users_processed.csv"
)

combined_data.to_csv(
    output_file,
    index=False
)

# ==============================
# SUMMARY
# ==============================

print("\nFeatures used:")

for feature in FEATURES:
    print(" -", feature)

print("\nLabels:")

print("1 = Genuine User (User 1)")
print("0 = Impostor (User 2)")

print("\nUser distribution:")

print(
    combined_data["user_id"].value_counts()
)

print("\nLabel distribution:")

print(
    combined_data["label"].value_counts()
)

print("\nSession count:")

print(
    combined_data["session"].nunique()
)

print("\nProcessed file saved at:")

print(output_file)

print("\n" + "=" * 60)
print("PREPROCESSING COMPLETED")
print("=" * 60)