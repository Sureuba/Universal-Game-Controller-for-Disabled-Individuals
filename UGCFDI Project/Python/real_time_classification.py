"""
real_time_classification.py

This script reads sensor data from the serial port (COM4),
processes a sliding window of data, extracts enhanced features,
and uses the trained model to predict a movement.
When a high-confidence prediction is made:
    - 'clench' → send the command "jump"
    - 'wrist'  → send the command "duck"
The command is sent to the game via a TCP socket connection.
"""

import serial
import time
import numpy as np
import tensorflow as tf
import socket
from collections import deque

# Set to True to simulate predictions (for debugging)
SIMULATE = True

# Connect to the game server (assumes the game is running a server on localhost:9999)
HOST = '127.0.0.1'
PORT = 9999

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False
while not connected:
    try:
        client_socket.connect((HOST, PORT))
        connected = True
        print(f"Connected to game server at {HOST}:{PORT}")
    except Exception as e:
        print("Connection to game server failed, retrying in 1 sec...")
        time.sleep(1)

# Load the trained model
model = tf.keras.models.load_model("emg_classifier.h5")
# Define label classes (update based on your actual labels)
label_classes = ['clench', 'rest', 'wrist']

# Parameters for the sliding window
WINDOW_SIZE = 100        # Number of samples in each window
OVERLAP_PERCENTAGE = 0   # 0% overlap between windows
CONFIDENCE_THRESHOLD = 0.7  # Only report predictions above this confidence

data_buffer = deque(maxlen=WINDOW_SIZE)
timestamps_buffer = deque(maxlen=WINDOW_SIZE)

if not SIMULATE:
    # Open serial connection (adjust port if necessary)
    try:
        ser = serial.Serial('COM4', 9600)
        ser.flushInput()
        time.sleep(0.5)
        print("Serial connection opened on COM4")
    except Exception as e:
        print("Failed to open serial connection on COM4:", e)
else:
    print("Simulation mode is ON. No serial connection will be used.")

def extract_features(window, timestamps):
    """
    Extract enhanced features from sensor values.
    Features: AUC, mean, std, RMS, max, min, mean derivative, std derivative.
    """
    window = np.array(window)
    timestamps = np.array(timestamps)
    
    auc = np.trapezoid(window, timestamps) if len(timestamps) > 1 else 0
    mean_val = np.mean(window)
    std_val = np.std(window)
    rms_val = np.sqrt(np.mean(np.square(window)))
    max_val = np.max(window)
    min_val = np.min(window)
    
    derivative = np.diff(window)
    mean_deriv = np.mean(derivative) if len(derivative) > 0 else 0
    std_deriv = np.std(derivative) if len(derivative) > 0 else 0
    
    features = np.array([auc, mean_val, std_val, rms_val, max_val, min_val, mean_deriv, std_deriv])
    return features.reshape(1, -1)

def run_classification():
    """
    Runs the classification loop: reads serial data (or simulates it), predicts movement,
    and sends a command to the game server via socket.
    """
    print("Starting real-time classification. Press Ctrl+C to stop.")
    last_prediction = None
    last_prediction_time = 0
    prediction_cooldown = 0.5  # seconds between reporting same prediction

    try:
        if SIMULATE:
            # In simulation mode, send a command every 2 seconds.
            import random
            while True:
                time.sleep(2)
                simulated_label = random.choice(['clench', 'rest', 'wrist'])
                print(f"Simulated prediction: {simulated_label}")
                if simulated_label == 'clench':
                    client_socket.sendall(b'jump')
                    print("Sent command: jump")
                elif simulated_label == 'wrist':
                    client_socket.sendall(b'duck')
                    print("Sent command: duck")
                # No commands sent for other labels.
        else:
            while True:
                line = ser.readline().decode('latin-1').strip()
                if not line:
                    # No data received; print debug info.
                    print("No data received from serial port.")
                    continue
                try:
                    value = int(line)
                except Exception as e:
                    print(f"Could not convert line to int: '{line}'. Error: {e}")
                    continue

                current_time = time.time()
                data_buffer.append(value)
                timestamps_buffer.append(current_time)
                
                if len(data_buffer) >= WINDOW_SIZE:
                    features = extract_features(list(data_buffer), list(timestamps_buffer))
                    prediction = model.predict(features)
                    max_prob = np.max(prediction)
                    predicted_label = label_classes[np.argmax(prediction)]
                    
                    if (max_prob > CONFIDENCE_THRESHOLD and 
                        (current_time - last_prediction_time > prediction_cooldown or 
                         predicted_label != last_prediction)):
                        print(f"Predicted movement: {predicted_label} (Confidence: {max_prob:.2f})")
                        last_prediction = predicted_label
                        last_prediction_time = current_time
                        
                        # Send command to game server via socket based on prediction
                        if predicted_label == 'clench':
                            client_socket.sendall(b'jump')
                            print("Detected clench → Sent command: jump")
                        elif predicted_label == 'wrist':
                            client_socket.sendall(b'duck')
                            print("Detected wrist → Sent command: duck")
                        else:
                            client_socket.sendall(b'run')
                            print("Detected normal → Sent command: run")
                    
                    # Slide the window
                    slide_amount = int(WINDOW_SIZE * (1 - OVERLAP_PERCENTAGE))
                    data_buffer = deque(list(data_buffer)[slide_amount:], maxlen=WINDOW_SIZE)
                    timestamps_buffer = deque(list(timestamps_buffer)[slide_amount:], maxlen=WINDOW_SIZE)
    except KeyboardInterrupt:
        print("Exiting real-time classification...")
    except Exception as e:
        print("Error in run_classification loop:", e)
    finally:
        if not SIMULATE:
            ser.close()
        client_socket.close()

if __name__ == "__main__":
    run_classification()
