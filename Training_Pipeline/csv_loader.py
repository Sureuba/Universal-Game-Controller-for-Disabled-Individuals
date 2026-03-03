#csv_loader.py

import torch
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List
from Architecture.config import Config

def load_csv_data_split(
    data_dir: str,
    window_size: int = Config.window_size,
    overlap: float = Config.overlap,
    train_split: float = Config.train_split
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Load CSV files and split by FILE (not by window) to prevent data leakage.
    
    Args:
        data_dir: Path to folder containing CSV files
        window_size: Samples per window (default from Config)
        overlap: Window overlap fraction (default from Config)
        train_split: Train/val split ratio (default from Config)
    
    Returns:
        train_windows, train_labels, val_windows, val_labels
    """
    
    gesture_map = {
        'rest': 0,
        'clench': 1,
        'wrist': 2
    }
    
    data_path = Path(data_dir)
    
    # Group files by gesture
    files_by_gesture = {
        'rest': list(data_path.glob('data_rest_*.csv')),
        'clench': list(data_path.glob('data_clench_*.csv')),
        'wrist': list(data_path.glob('data_wrist_*.csv'))
    }
    
    train_windows = []
    train_labels = []
    val_windows = []
    val_labels = []
    
    # Process each gesture separately
    for gesture_name, files in files_by_gesture.items():
        gesture_label = gesture_map[gesture_name]
        
        # Split files (not windows) to prevent data leakage
        num_train = int(len(files) * train_split)
        train_files = files[:num_train]
        val_files = files[num_train:]
        
        print(f"\n{gesture_name.upper()}:")
        print(f"  Train files: {len(train_files)}")
        print(f"  Val files:   {len(val_files)}")
        
        # Process training files
        for csv_file in train_files:
            windows = process_file(csv_file, window_size, overlap)
            train_windows.extend(windows)
            train_labels.extend([gesture_label] * len(windows))
        
        # Process validation files
        for csv_file in val_files:
            windows = process_file(csv_file, window_size, overlap)
            val_windows.extend(windows)
            val_labels.extend([gesture_label] * len(windows))
    
    # Convert to tensors [N, num_channels, window_size]
    train_windows = np.array(train_windows)[:, np.newaxis, :]
    val_windows = np.array(val_windows)[:, np.newaxis, :]
    
    train_windows_tensor = torch.tensor(train_windows, dtype=torch.float32)
    train_labels_tensor = torch.tensor(train_labels, dtype=torch.long)
    val_windows_tensor = torch.tensor(val_windows, dtype=torch.float32)
    val_labels_tensor = torch.tensor(val_labels, dtype=torch.long)
    
    print(f"\n=== FINAL SPLIT ===")
    print(f"Train: {len(train_windows_tensor)} windows")
    print(f"  Rest: {(train_labels_tensor == 0).sum()}")
    print(f"  Clench: {(train_labels_tensor == 1).sum()}")
    print(f"  Wrist: {(train_labels_tensor == 2).sum()}")
    print(f"\nVal: {len(val_windows_tensor)} windows")
    print(f"  Rest: {(val_labels_tensor == 0).sum()}")
    print(f"  Clench: {(val_labels_tensor == 1).sum()}")
    print(f"  Wrist: {(val_labels_tensor == 2).sum()}")
    
    return train_windows_tensor, train_labels_tensor, val_windows_tensor, val_labels_tensor


def process_file(csv_file: Path, window_size: int, overlap: float) -> List[np.ndarray]:
    """
    Process one CSV file into overlapping windows.
    
    Args:
        csv_file: Path to CSV file
        window_size: Samples per window
        overlap: Overlap fraction (0.75 = 75% overlap)
    
    Returns:
        List of windows (numpy arrays)
    """
    df = pd.read_csv(csv_file)
    values = df['value'].values

    # Convert ADC (0-1023) to voltage only — do NOT center the whole file
    voltages = (values / 1023.0) * 5.0  # ADC → 0-5V

    # Create overlapping windows, centering each window individually
    # This matches inference exactly: interference_engine.preprocess_window()
    # centers by the mean of that 200-sample window, not the whole recording
    stride = int(window_size * (1 - overlap))
    windows = []

    for start in range(0, len(voltages) - window_size, stride):
        window = voltages[start:start + window_size]
        if len(window) == window_size:
            window = (window - np.mean(window)) * 1000  # center this window, convert to mV
            windows.append(window)
    
    return windows


if __name__ == '__main__':
    # Test with Config defaults
    train_w, train_l, val_w, val_l = load_csv_data_split('data')
    print(f"\nTrain shape: {train_w.shape}")
    print(f"Val shape: {val_w.shape}")