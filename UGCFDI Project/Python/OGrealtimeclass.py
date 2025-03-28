"""
real_time_classification.py

This script performs real-time classification by reading sensor data from the serial port,
processing a sliding window of data, and using the trained model to predict the movement.
"""

import serial
import time
import numpy as np
import tensorflow as tf
from collections import deque

# Load the trained model
model = tf.keras.models.load_model("emg_classifier.h5")
# Define label classes as per the training (update these based on the labels)
label_classes = ['rest', 'clench', 'open', 'index', 'bicepCurl']  

# Parameters for the sliding window
window_size = 500  # Number of samples in each window corresponds to 4s ish
data_buffer = deque(maxlen=window_size)

# Open serial connection (adjust port if necessary)
ser = serial.Serial('COM4', 9600)
ser.flushInput()
time.sleep(0.5)

def extract_features(window):
    """Extract features from a list of sensor values."""
    window = np.array(window)
    mean_val = np.mean(window)
    std_val = np.std(window)
    rms_val = np.sqrt(np.mean(np.square(window)))
    max_val = np.max(window)
    min_val = np.min(window)
    return np.array([mean_val, std_val, rms_val, max_val, min_val]).reshape(1, -1)

print("Starting real-time classification. Press Ctrl+C to stop.")
try:
    while True:
        line = ser.readline().decode('latin-1').strip()

        try:
            value = int(line)
            data_buffer.append(value)
            # Once we have enough samples, extract features and classify
            if len(data_buffer) >= window_size:
                # print(data_buffer)
                features = extract_features(list(data_buffer))
                prediction = model.predict(features)
                predicted_label = label_classes[np.argmax(prediction)]
                print(f"Predicted movement: {predicted_label}")
                data_buffer.clear()
        except Exception as e:
            continue  # Skip any lines that cause errors
except KeyboardInterrupt:
    print("Exiting real-time classification...")
ser.close()

# model.predict(features) : returns a probability vector, argmax picks the highest
