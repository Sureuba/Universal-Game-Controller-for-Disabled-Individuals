"""
real_time_classification.py

This script performs real-time classification by reading sensor data from the serial port,
processing a sliding window of data, extracting enhanced features (basic, fTDD, TSD, and wavelet-based),
and using the trained model to predict the movement.
"""

import serial
import time
import numpy as np
import tensorflow as tf
import pywt
from collections import deque

# Load the trained model
model = tf.keras.models.load_model("emg_classifier.h5")
# Define label classes as per the training (update these based on your actual labels)
label_classes = ['clench', 'index', 'rest','wrist']  # Example labels; update as needed

# Parameters for the sliding window and predictions
WINDOW_SIZE = 200          # Number of samples in each window
OVERLAP_PERCENTAGE = 0     # e.g., 0.0 for no overlap, 0.5 for 50% overlap
CONFIDENCE_THRESHOLD = 0.7 # Only report predictions above this confidence

data_buffer = deque(maxlen=WINDOW_SIZE)
timestamps_buffer = deque(maxlen=WINDOW_SIZE)

# Open serial connection (adjust port and baudrate as necessary)
ser = serial.Serial('COM4', 9600)
ser.flushInput()
time.sleep(0.5)

def extract_features(window, timestamps):
    """
    Extract enhanced features from a list of sensor values and their timestamps.
    The features extracted are:
    - Basic: AUC, mean, std, RMS, max, min, mean derivative, std derivative
    - fTDD: ps_moment1, ps_moment2, sparsity, irregularity_factor, waveform_length_ratio
    - TSD: coefficient of variation (cov), Teager-Kaiser Energy Operator (tkeo)
    - Wavelet-based: wavelet_energy, wavelet_variance, wavelet_std, wavelet_wl, wavelet_entropy
    Returns a numpy array of shape (1, 20) to be fed into the model.
    """
    window = np.array(window)
    n = len(window)
    timestamps = np.array(timestamps)
    
    # Compute time interval dt from timestamps, if possible
    if len(timestamps) > 1:
        dt = np.mean(np.diff(timestamps))
    else:
        dt = 1

    # --- Basic Features ---
    auc = np.trapz(window, dx=dt)
    mean_val = np.mean(window)
    std_val = np.std(window)
    rms_val = np.sqrt(np.mean(np.square(window)))
    max_val = np.max(window)
    min_val = np.min(window)
    
    derivative = np.diff(window)
    if len(derivative) > 0:
        mean_deriv = np.mean(derivative)
        std_deriv = np.std(derivative)
    else:
        mean_deriv = 0
        std_deriv = 0

    # --- fTDD Features ---
    fft_vals = np.fft.fft(window)
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

    norm1 = np.linalg.norm(window, 1)
    norm2 = np.linalg.norm(window, 2)
    if norm2 > 0 and n > 1:
        sparsity = (np.sqrt(n) - (norm1 / norm2)) / (np.sqrt(n) - 1)
    else:
        sparsity = 0

    if len(derivative) > 0:
        mean_abs_deriv = np.mean(np.abs(derivative))
        irregularity_factor = std_deriv / (mean_abs_deriv if mean_abs_deriv != 0 else 1)
    else:
        irregularity_factor = 0

    waveform_length = np.sum(np.abs(np.diff(window)))
    amplitude_range = max_val - min_val if (max_val - min_val) != 0 else 1
    waveform_length_ratio = waveform_length / amplitude_range

    # --- TSD Features ---
    cov = std_val / mean_val if mean_val != 0 else 0
    if n >= 3:
        tkeo_values = window[1:-1]**2 - window[:-2] * window[2:]
        tkeo = np.mean(tkeo_values)
    else:
        tkeo = 0

    # --- Wavelet Transform-Based Features ---
    try:
        coeffs = pywt.wavedec(window, 'db4', level=3)
        # Use detail coefficients at level 3 (first detail coefficient after approximation)
        if len(coeffs) > 1:
            detail_coeffs = coeffs[1]
        else:
            detail_coeffs = np.array([])
    except Exception:
        detail_coeffs = np.array([])

    if detail_coeffs.size > 0:
        wavelet_energy = np.sum(detail_coeffs**2)
        wavelet_variance = np.var(detail_coeffs)
        wavelet_std = np.std(detail_coeffs)
        wavelet_wl = np.sum(np.abs(np.diff(detail_coeffs)))
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

    # Create feature vector in the same order as during training:
    # [auc, mean, std, rms, max, min, mean_deriv, std_deriv,
    #  ps_moment1, ps_moment2, sparsity, irregularity_factor, waveform_length_ratio,
    #  cov, tkeo, wavelet_energy, wavelet_variance, wavelet_std, wavelet_wl, wavelet_entropy]
    features = np.array([
        auc, mean_val, std_val, rms_val, max_val, min_val, mean_deriv, std_deriv,
        ps_moment1, ps_moment2, sparsity, irregularity_factor, waveform_length_ratio,
        cov, tkeo, wavelet_energy, wavelet_variance, wavelet_std, wavelet_wl, wavelet_entropy
    ])
    return features.reshape(1, -1)

print("Starting real-time classification. Press Ctrl+C to stop.")

last_prediction = None
last_prediction_time = 0
prediction_cooldown = 0.5  # Seconds between reporting the same prediction

try:
    while True:
        line = ser.readline().decode('latin-1').strip()
        try:
            # Parse the incoming sensor value; adjust type conversion as needed (e.g., float)
            value = float(line)
            current_time = time.time()

            data_buffer.append(value)
            timestamps_buffer.append(current_time)

            # Once the buffer is full, extract features and classify
            if len(data_buffer) >= WINDOW_SIZE:
                features = extract_features(list(data_buffer), list(timestamps_buffer))
                prediction = model.predict(features)
                max_prob = np.max(prediction)
                predicted_label = label_classes[np.argmax(prediction)]
                
                # Report prediction if confidence is high and either not repeated too quickly
                # or the prediction has changed
                if (max_prob > CONFIDENCE_THRESHOLD and 
                    (current_time - last_prediction_time > prediction_cooldown or 
                     predicted_label != last_prediction)):
                    print(f"Predicted movement: {predicted_label} (Confidence: {max_prob:.2f})")
                    last_prediction = predicted_label
                    last_prediction_time = current_time

                # Slide the window (adjust overlap as desired)
                slide_amount = int(WINDOW_SIZE * (1 - OVERLAP_PERCENTAGE))
                data_buffer = deque(list(data_buffer)[slide_amount:], maxlen=WINDOW_SIZE)
                timestamps_buffer = deque(list(timestamps_buffer)[slide_amount:], maxlen=WINDOW_SIZE)
        except Exception:
            continue

except KeyboardInterrupt:
    print("Exiting real-time classification...")
    ser.close()
