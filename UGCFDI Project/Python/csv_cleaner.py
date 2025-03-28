import os
import glob
import pandas as pd

# Define the threshold for outliers
THRESHOLD = 400

# Define input and output folders
input_folder = "data_being_modified"
output_folder = "cleaned_data"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Get all CSV files in the input folder
csv_files = glob.glob(os.path.join(input_folder, "*.csv"))

for file_path in csv_files:
    print(f"Processing file: {file_path}")
    # Load the CSV file
    df = pd.read_csv(file_path)
    
    # Check if the required column exists
    if 'value' not in df.columns:
        print(f"Skipping {file_path}: 'value' column not found.")
        continue

    # Iterate over each row to check for outliers
    for i in range(len(df)):
        current_value = df.loc[i, 'value']
        if current_value > THRESHOLD:
            # Determine the new value by interpolating between the previous and next valid points.
            if i == 0 and len(df) > 1:
                new_value = df.loc[i + 1, 'value']
            elif i == len(df) - 1 and i > 0:
                new_value = df.loc[i - 1, 'value']
            elif i > 0 and i < len(df) - 1:
                new_value = (df.loc[i - 1, 'value'] + df.loc[i + 1, 'value']) / 2
            else:
                new_value = current_value  # Fallback if neither neighbor exists

            print(f"Replacing outlier at index {i}: {current_value} -> {new_value}")
            df.loc[i, 'value'] = new_value

    # Save the cleaned file to the output folder using the same filename
    base_filename = os.path.basename(file_path)
    output_path = os.path.join(output_folder, base_filename)
    df.to_csv(output_path, index=False)
    print(f"Saved cleaned file to: {output_path}")
