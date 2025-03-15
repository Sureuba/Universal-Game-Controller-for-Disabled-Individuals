import tkinter as tk
from tkinter import ttk

class Frame6(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Frame 6")
        self.geometry("500x500")

        label = ttk.Label(self, text="Motion capture successful!") 
        label.pack(pady=20)

        button = ttk.Button(self, text="Back", command=self.on_button_click)
        button.pack(pady=10)

    def on_button_click(self):
        print("Button clicked!")

if __name__ == "__main__":
    app = Frame6()
    app.mainloop()