"""
data_preprocessing.py

This script scans the 'data' folder for CSV files of raw sensor data,
extracts enhanced features (basic features, fTDD, TSD, and wavelet-based features),
and outputs a combined features.csv file.

Assumes each file is named in the format: data_<label>_<timestamp>.csv
"""

import os
import glob
import pandas as pd
import numpy as np
import pywt

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
    n = len(values)
    if n == 0:
        continue
    
    # Compute AUC using the trapezoidal rule
    if 'timestamp' in df.columns:
        timestamps = df['timestamp'].values
        auc = np.trapezoid(values, timestamps)
        dt = np.mean(np.diff(timestamps)) if len(timestamps) > 1 else 1
    else:
        auc = np.trapezoid(values)
        dt = 1

    # Basic features
    mean_val = np.mean(values)
    std_val = np.std(values)
    rms_val = np.sqrt(np.mean(np.square(values)))
    max_val = np.max(values)
    min_val = np.min(values)
    
    # Compute first derivative of the signal and its statistics
    derivative = np.diff(values)
    if len(derivative) > 0:
        mean_deriv = np.mean(derivative)
        std_deriv = np.std(derivative)
    else:
        mean_deriv = 0
        std_deriv = 0
    
    # fTDD Features:
    # Power Spectral Moments (using FFT)
    fft_vals = np.fft.fft(values)
    power_spectrum = np.abs(fft_vals)**2
    freqs = np.fft.fftfreq(n, d=dt)
    pos_mask = freqs >= 0
    pos_freqs = freqs[pos_mask]
    pos_power = power_spectrum[pos_mask]
    total_power = np.sum(pos_power)
    if total_power > 0:
        ps_moment1 = np.sum(pos_freqs * pos_power) / total_power
        ps_moment2 = np.sqrt(np.sum(((pos_freqs - ps_moment1)**2) * pos_power) / total_power)
    else:
        ps_moment1 = 0
        ps_moment2 = 0

    # Sparsity (Hoyer's measure)
    norm1 = np.linalg.norm(values, 1)
    norm2 = np.linalg.norm(values, 2)
    if norm2 > 0 and n > 1:
        sparsity = (np.sqrt(n) - (norm1 / norm2)) / (np.sqrt(n) - 1)
    else:
        sparsity = 0

    # Irregularity Factor: ratio of std(derivative) to mean(abs(derivative))
    if len(derivative) > 0:
        mean_abs_deriv = np.mean(np.abs(derivative))
        irregularity_factor = std_deriv / mean_abs_deriv if mean_abs_deriv != 0 else 0
    else:
        irregularity_factor = 0

    # Waveform Length Ratio: waveform length divided by amplitude range
    waveform_length = np.sum(np.abs(np.diff(values)))
    amplitude_range = max_val - min_val if (max_val - min_val) != 0 else 1
    waveform_length_ratio = waveform_length / amplitude_range

    # TSD Features:
    # Coefficient of Variation (COV)
    cov = std_val / mean_val if mean_val != 0 else 0

    # Teager-Kaiser Energy Operator (TKEO)
    if n >= 3:
        tkeo_values = values[1:-1]**2 - values[:-2] * values[2:]
        tkeo = np.mean(tkeo_values)
    else:
        tkeo = 0

    # Wavelet Transform Based Features:
    # Perform wavelet decomposition using 'db4' up to level 3 if possible
    try:
        coeffs = pywt.wavedec(values, 'db4', level=3)
        # Use detail coefficients at level 3 (first detail coefficient after approximation)
        if len(coeffs) > 1:
            detail_coeffs = coeffs[1]
        else:
            detail_coeffs = np.array([])
    except Exception as e:
        detail_coeffs = np.array([])

    if detail_coeffs.size > 0:
        wavelet_energy = np.sum(detail_coeffs**2)
        wavelet_variance = np.var(detail_coeffs)
        wavelet_std = np.std(detail_coeffs)
        wavelet_wl = np.sum(np.abs(np.diff(detail_coeffs)))
        # Compute entropy of the wavelet coefficients
        power = detail_coeffs**2
        total_power_wavelet = np.sum(power)
        if total_power_wavelet > 0:
            p_norm = power / total_power_wavelet
            wavelet_entropy = -np.sum(p_norm * np.log(p_norm + 1e-12))
        else:
            wavelet_entropy = 0
    else:
        wavelet_energy = 0
        wavelet_variance = 0
        wavelet_std = 0
        wavelet_wl = 0
        wavelet_entropy = 0

    # Append all features to the list
    rows.append({
        "label": label, 
        "auc": auc,
        "mean": mean_val, 
        "std": std_val, 
        "rms": rms_val,
        "max": max_val,
        "min": min_val,
        "mean_deriv": mean_deriv,
        "std_deriv": std_deriv,
        "ps_moment1": ps_moment1,
        "ps_moment2": ps_moment2,
        "sparsity": sparsity,
        "irregularity_factor": irregularity_factor,
        "waveform_length_ratio": waveform_length_ratio,
        "cov": cov,
        "tkeo": tkeo,
        "wavelet_energy": wavelet_energy,
        "wavelet_variance": wavelet_variance,
        "wavelet_std": wavelet_std,
        "wavelet_wl": wavelet_wl,
        "wavelet_entropy": wavelet_entropy
    })

features_df = pd.DataFrame(rows)
features_df.to_csv("features.csv", index=False)
print("Features saved to features.csv")
