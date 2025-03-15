import tkinter as tk

def open_popup():
    # Create a new top-level window (popup)
    popup = tk.Toplevel(root)
    popup.title("Popup Window")
    popup.geometry("300x150")
    
    # Add a label with some text in the middle of the popup
    label = tk.Label(popup, text="This is a popup message!", font=("Helvetica", 14))
    label.pack(pady=20)
    
    # Add a button that closes the popup window
    close_button = tk.Button(popup, text="Close", command=popup.destroy)
    close_button.pack(pady=10)

# Main application window
root = tk.Tk()
root.title("Main Window")
root.geometry("400x500")

# Button to open the popup window
open_popup_button = tk.Button(root, text="Open Popup", command=open_popup)
open_popup_button.pack(pady=50)

root.mainloop()

