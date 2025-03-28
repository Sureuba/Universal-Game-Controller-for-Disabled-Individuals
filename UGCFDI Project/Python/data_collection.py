"""
data_collection.py

This script reads EMG sensor values from the serial port for a specified duration.
It accumulates the data in memory and then saves it to a CSV file only if none of the 
recorded values exceed 500. Otherwise, the file is not saved.
Usage: python data_collection.py --label <movement_label> --duration <sec
Example: python data_collection.py --label openR --duration 4
"""

import serial
import csv
import time
import argparse
import os

# Set up command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=str, default='COM4', help='Serial port (e.g., COM4 or /dev/ttyACM0)')
parser.add_argument('--baud', type=int, default=9600, help='Baud rate')
parser.add_argument('--label', type=str, required=True, help='Label for the movement (e.g., index_finger_up)')
parser.add_argument('--duration', type=int, default=30, help='Recording duration in seconds')
args = parser.parse_args()

# Initialize serial communication for collecting data from muscle sensor 
ser = serial.Serial(args.port, args.baud)
ser.flushInput()
time.sleep(2)  # Wait for the connection to establish
print("Connection is established")

# Counter for file naming (if needed)
counter = 1

while True:
    # Collect data in a list (instead of writing immediately to file)
    data_rows = []
    start_time = time.time()
    while time.time() - start_time < args.duration:
        line = ser.readline().decode('latin-1').strip()
        print(line)
        try:
            value = int(line)
            timestamp_value = time.time()
            data_rows.append([timestamp_value, value])
        except ValueError:
            continue  # Skip lines that cannot be converted to int

    # Check if any reading exceeds the threshold (500)
    if any(row[1] > 900 for row in data_rows):
        print("Data contains values above 900; CSV file will not be saved.")
    else:
        if any(row[1] > 450 for row in data_rows):
            print("IT HAS OVER 450")
        # Create a new filename for the run using the label and the current timestamp
        filename = f"data_{args.label}_{int(time.time())}.csv"
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["timestamp", "value"])  # CSV header
            for row in data_rows:
                writer.writerow(row)
        print(f"Data saved to {filename}")

    # Ask the user if they want to continue
    user_input = input("Do you want to continue? (Y/N): ")
    if user_input.lower() != 'y':
        break

    counter += 1

ser.close()
