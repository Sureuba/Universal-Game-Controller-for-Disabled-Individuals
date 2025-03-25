"""
data_collection.py

This script reads EMG sensor values from the serial port and saves them to a CSV file.
Usage: python data_collection.py --label <movement_label> --duration <seconds>
Example: python data_collection.py --label index_finger_up --duration 30
"""

import serial
import csv
import time
import argparse

# Set up command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=str, default='COM4', help='Serial port (e.g., COM4 or /dev/ttyACM0)')
parser.add_argument('--baud', type=int, default=9600, help='Baud rate')
parser.add_argument('--label', type=str, required=True, help='Label for the movement (e.g., index_finger_up)')
parser.add_argument('--duration', type=int, default=30, help='Recording duration in seconds')
args = parser.parse_args()

# Initialize serial communication
ser = serial.Serial(args.port, args.baud)
ser.flushInput()
time.sleep(0.5)  # Wait for the connection to establish
print("Connection is established")


filename = f"data_{args.label}_{int(time.time())}.csv"
with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["timestamp", "value"])  # CSV header
    start_time = time.time()
    while time.time() - start_time < args.duration:
        line = ser.readline().strip()
        try:
            value = int(line)
            writer.writerow([time.time(), value])
        except ValueError:
            continue  # Skip lines that cannot be converted to int

print(f"Data saved to {filename}")
ser.close()
