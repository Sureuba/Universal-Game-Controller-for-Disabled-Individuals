import pandas as pd

import matplotlib.pyplot as plt

def graph_csv_data(csv_path):
    """
    Graph voltage vs time from a CSV file.
    
    Args:
        csv_path (str): Path to the CSV file with 'timestamp' and 'value' columns
    """
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['value'], linewidth=2)
    
    # Label axes and title
    plt.xlabel('Time (timestamp)', fontsize=12)
    plt.ylabel('Voltage', fontsize=12)
    plt.title('Voltage vs Time', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # Display the plot
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    csv_file = input("Enter the path to your CSV file: ")
    graph_csv_data(csv_file)