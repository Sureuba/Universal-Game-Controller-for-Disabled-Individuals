import os
import csv
import re

# Specify the folder containing your files.
# For example, if the files are in a folder named "data" in the current directory:
folder = "data_being_modified"  # Change this as needed; use "." for current directory.

# Loop through all files in the folder
for filename in os.listdir(folder):
    # Match files that start with "clenchNav" and optionally followed by digits,
    # with or without a file extension.
    if re.match(r'^restNav\d*$', filename) or re.match(r'^restNav\d*\.csv$', filename):
        file_path = os.path.join(folder, filename)
        print(f"Processing file: {filename}")
        
        # Open the file and read the first row of data.
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            # Attempt to get the first row
            first_row = next(reader, None)
            if first_row is None:
                print(f"{filename} is empty, skipping.")
                continue
            
            # Check if the file contains a header (e.g., "timestamp") in the first column.
            if first_row[0].strip().lower() == "timestamp":
                # Read the next row to get the first data value.
                data_row = next(reader, None)
                if data_row is None:
                    print(f"{filename} has a header only, skipping.")
                    continue
                timestamp_str = data_row[0].strip()
            else:
                # No header; assume the first element of the first row is the timestamp.
                timestamp_str = first_row[0].strip()
        
        # Convert the timestamp to an integer (dropping any decimal part)
        try:
            timestamp_int = int(float(timestamp_str))
        except ValueError:
            print(f"Could not convert timestamp in {filename}: {timestamp_str}")
            continue
        
        # Build the new filename: data_clench_<timestamp>.csv
        new_filename = f"data_rest_{timestamp_int}.csv"
        new_file_path = os.path.join(folder, new_filename)
        
        print(f"Renaming {filename} to {new_filename}")
        os.rename(file_path, new_file_path)
