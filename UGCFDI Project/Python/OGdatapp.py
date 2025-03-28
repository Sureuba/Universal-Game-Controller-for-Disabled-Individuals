"""
data_preprocessing.py

This script scans the 'data' folder for CSV files of raw sensor data,
extracts features, 
and outputs a combined features.csv file.

Assumes each file is named in the format: data_<label>_<timestamp>.csv
"""

import os
import glob
import pandas as pd
import numpy as np

# Folder where raw data CSVs are stored (create this folder and move your CSV files here)
data_folder = "data"
files = glob.glob(os.path.join(data_folder, "*.csv"))

rows = []
for file in files:
    # Extract label from filename: expected pattern: data_<label>_<timestamp>.csv
    basename = os.path.basename(file)
    parts = basename.split('_')
    if len(parts) < 3:
        continue
    label = parts[1]
    df = pd.read_csv(file)
    if 'value' not in df.columns:
        continue
    values = df['value'].values
    
    # Compute features: mean, standard deviation, RMS, max, min used for Layer 1 
    mean_val = np.mean(values)
    std_val = np.std(values)
    rms_val = np.sqrt(np.mean(np.square(values)))
    max_val = np.max(values)
    min_val = np.min(values)
    rows.append({"label": label, "mean": mean_val, "std": std_val, "rms": rms_val, "max": max_val, "min": min_val})

features_df = pd.DataFrame(rows)
features_df.to_csv("features.csv", index=False)
print("Features saved to features.csv")
