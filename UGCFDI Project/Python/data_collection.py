"""
data_collection.py

This script reads EMG sensor values from the serial port and saves them to a CSV file.
Usage: python data_collection.py --label <movement_label> --duration <seconds>
Example: python data_collection.py --label openR --duration 4
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
<<<<<<< HEAD
print("connected")
time.sleep(2)  # Wait for the connection to establish
=======
ser.flushInput()
time.sleep(0.5)  # Wait for the connection to establish
print("Connection is established")
>>>>>>> 2b8b17a60b8edd0185a9e2ca8a9ba2a84f45545f

<<<<<<< HEAD
=======
# Counter for file naming
counter = 1
>>>>>>> 2b8b17a60b8edd0185a9e2ca8a9ba2a84f45545f

<<<<<<< HEAD

# FILE OUTPUT 
print("writing data now")
filename = f"data_{args.label}_{int(time.time())}.csv"
with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["timestamp", "value"])  # CSV header
    start_time = time.time()
    while time.time() - start_time < args.duration:
        line = ser.readline().decode('utf-8').strip()
        try:
            value = int(line)
            writer.writerow([time.time(), value])
            print("finished writing")
        except ValueError:
            continue  # Skip lines that cannot be converted to int
=======
while True:
    # Create a new filename for each run using the label and the counter
    filename = f"{args.label}{counter}.csv"
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
>>>>>>> 2b8b17a60b8edd0185a9e2ca8a9ba2a84f45545f

<<<<<<< HEAD

print(f"Data saved to {filename}")
=======
    print(f"Data saved to {filename}")

    # Ask the user if they want to continue
    user_input = input("Do you want to continue? (Y/N): ")
    if user_input.lower() != 'y':
        break

    counter += 1

>>>>>>> 2b8b17a60b8edd0185a9e2ca8a9ba2a84f45545f
ser.close()
