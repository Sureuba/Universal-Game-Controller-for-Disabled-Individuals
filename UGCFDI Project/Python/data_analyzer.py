import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

# Load the CSV file. Adjust the filename if needed.
# UGCFDI Project/Python/data_bicepCurlTEST8_1742865503.csv
filename = "data_indexR1_1742948114.csv"
df = pd.read_csv(filename)

# Display the first few rows to confirm the data was loaded correctly.
print(df.head())

# Create the matplotlib figure and axis.
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df["timestamp"], df["value"], marker="o", linestyle="-")
ax.set_xlabel("Timestamp")
ax.set_ylabel("Voltage")
ax.set_title("Time vs Voltage")
ax.grid(True)

# Create a Tkinter window.
root = tk.Tk()x
root.title("Time vs Voltage Plot")

# Embed the matplotlib figure in the Tkinter window.
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Start the Tkinter main loop.
tk.mainloop()
# UGCFDI Project/Python/data_bicepCurlTEST7_1742865483.csv