import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file. Adjust the filename if needed.
filename = "data_bicepCurlTEST4.csv"
df = pd.read_csv(filename)

# Display the first few rows to confirm the data was loaded correctly.
print(df.head())

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(df["timestamp"], df["value"], marker="o", linestyle="-")
plt.xlabel("Timestamp")
plt.ylabel("Voltage")
plt.title("Time vs Voltage")
plt.grid(True)
plt.show()
