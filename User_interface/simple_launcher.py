# simple_launcher.py - Simple GUI Launcher with Game
import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
from pathlib import Path

class SimpleLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("EMG System Launcher")
        self.root.geometry("500x530")

        # Check status
        self.model_exists = Path('student_model_best.pth').exists()
        self.game_exists = Path('archive/dino_game.py').exists()
        self.canvas_exists = Path('Canvas/canvas_app.py').exists()
        self.data_exists = Path('data').exists() and len(list(Path('data').glob('*.csv'))) > 0
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        title = tk.Label(
            self.root,
            text="EMG GESTURE CONTROL",
            font=('Arial', 20, 'bold'),
            bg='lightblue'
        )
        title.pack(fill='x', pady=20)
        
        # Status Section
        status_frame = tk.LabelFrame(self.root, text="System Status", font=('Arial', 12, 'bold'))
        status_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(
            status_frame,
            text=f"✓ Training Data" if self.data_exists else "✗ Training Data (not collected)",
            font=('Arial', 10),
            fg='green' if self.data_exists else 'red'
        ).pack(anchor='w', padx=10, pady=2)

        tk.Label(
            status_frame,
            text=f"✓ Trained Model" if self.model_exists else "✗ Trained Model (not trained)",
            font=('Arial', 10),
            fg='green' if self.model_exists else 'red'
        ).pack(anchor='w', padx=10, pady=2)
        
        # Setup Section
        setup_frame = tk.LabelFrame(self.root, text="Setup Steps", font=('Arial', 12, 'bold'))
        setup_frame.pack(fill='x', padx=20, pady=10)

        tk.Button(
            setup_frame,
            text="1. Collect Training Data",
            width=35,
            height=2,
            command=self.run_collect,
            bg='lightgray'
        ).pack(pady=5, padx=10)

        tk.Button(
            setup_frame,
            text="2. Train Model",
            width=35,
            height=2,
            command=self.run_train,
            bg='lightgray'
        ).pack(pady=5, padx=10)
        
        # Play Section
        play_frame = tk.LabelFrame(self.root, text="Launch Application", font=('Arial', 12, 'bold'))
        play_frame.pack(fill='x', padx=20, pady=10)

        ready = self.model_exists

        # Dino game button
        dino_color = 'green' if (ready and self.game_exists) else 'gray'
        dino_state = 'normal' if (ready and self.game_exists) else 'disabled'
        tk.Button(
            play_frame,
            text="▶ DINO GAME",
            width=35,
            height=2,
            bg=dino_color,
            fg='white',
            font=('Arial', 11, 'bold'),
            command=self.play_game,
            state=dino_state,
        ).pack(pady=(10, 4), padx=10)
        tk.Label(play_frame, text="3-gesture control  |  jump / duck / run", font=('Arial', 9), fg='gray').pack()

        # Canvas button
        canvas_color = 'royalblue' if (ready and self.canvas_exists) else 'gray'
        canvas_state = 'normal' if (ready and self.canvas_exists) else 'disabled'
        tk.Button(
            play_frame,
            text="▶ EMG CANVAS",
            width=35,
            height=2,
            bg=canvas_color,
            fg='white',
            font=('Arial', 11, 'bold'),
            command=self.play_canvas,
            state=canvas_state,
        ).pack(pady=(10, 4), padx=10)
        tk.Label(play_frame, text="continuous visualizer  |  live waveform + probability bars", font=('Arial', 9), fg='gray').pack(pady=(0, 8))
    
    def run_collect(self):
        """Run data collection"""
        try:
            subprocess.Popen(
                [sys.executable, 'Generated_Files/collect_gesture_data.py'],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not run collection:\n{e}")

    def run_train(self):
        """Run training"""
        if not self.data_exists:
            messagebox.showwarning("Not Ready", "Please run 'Collect Data' first!")
            return
        try:
            subprocess.Popen(
                ['cmd', '/k', sys.executable, 'Training_Pipeline/main.py'],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not run training:\n{e}")
    
    def play_canvas(self):
        """Start the EMG canvas visualizer"""
        if not self.model_exists:
            messagebox.showwarning("Not Ready", "Please complete setup steps 1-2 first!")
            return
        if not self.canvas_exists:
            messagebox.showerror("Error", "Canvas/canvas_app.py not found!")
            return

        try:
            subprocess.Popen([sys.executable, 'Canvas/canvas_app.py'])
            print("[LAUNCHER] Canvas started!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not start canvas:\n{e}")
            return

        messagebox.showinfo(
            "Canvas Starting",
            "EMG Canvas window opened!\n\nStarting EMG control in 2 seconds...\n\nFlex your muscles to paint.\nSPACE = clear canvas"
        )
        self.root.after(2000, self.start_emg_canvas)

    def start_emg_canvas(self):
        """Start canvas EMG control"""
        try:
            subprocess.Popen([sys.executable, 'Canvas/real_time_emg_canvas.py'])
            messagebox.showinfo(
                "Canvas Ready!",
                "EMG canvas control is now active!\n\nYour muscle signals will paint the canvas.\nDifferent gestures = different colors.\nContraction strength = brush speed + size."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not start canvas EMG:\n{e}")

    def play_game(self):
        """Start game and EMG control"""
        if not self.model_exists:
            messagebox.showwarning("Not Ready", "Please complete setup steps 1-2 first!")
            return
        
        if not self.game_exists:
            messagebox.showerror("Error", "dino_game.py not found in this folder!")
            return
        
        # Start game first
        try:
            subprocess.Popen([sys.executable, 'archive/dino_game.py'])
            print("[LAUNCHER] Game started!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not start game:\n{e}")
            return
        
        # Wait 2 seconds, then start EMG control
        messagebox.showinfo(
            "Game Starting",
            "Dino game window opened!\n\nStarting EMG control in 2 seconds...\n\nControls:\n• Keyboard: SPACE=jump, DOWN=duck\n• EMG: Your muscle gestures"
        )
        
        self.root.after(2000, self.start_emg)
    
    def start_emg(self):
        """Start EMG control after game"""
        try:
            subprocess.Popen([sys.executable, 'Inference/real_time_emg.py'])
            messagebox.showinfo(
                "Ready to Play!",
                "EMG control is now active!\n\nPerform your gestures to control the dino.\n\nTo stop: Close the game window."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not start EMG control:\n{e}")


if __name__ == '__main__':
    root = tk.Tk()
    app = SimpleLauncher(root)
    root.mainloop()

