import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Project root — so paths work regardless of where this script is run from
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import matplotlib.pyplot as plt
from Training_Pipeline.csv_loader import load_csv_data_split
from Architecture.student_transformer import StudentTransformer
from Architecture.config import Config

# Device selection
device = 'cuda' if torch.cuda.is_available() else 'cpu'   #if gpu is there probably better
print(f"Using device: {device}")

# Load data (uses Config defaults)
print("\nLoading data...")
train_windows, train_labels, val_windows, val_labels = load_csv_data_split(os.path.join(PROJECT_ROOT, 'data'))

# Create dataloaders
train_dataset = TensorDataset(train_windows, train_labels)
val_dataset = TensorDataset(val_windows, val_labels)

train_loader = DataLoader(train_dataset, batch_size=Config.batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=Config.batch_size, shuffle=False)

# Create model (uses Config defaults)
print("\nCreating model...")
# Class weights: inverse frequency so under-represented classes get higher loss penalty.
# Normalized so the mean weight = 1 (keeps loss scale stable).
counts = torch.bincount(train_labels, minlength=Config.num_gestures).float()
class_weights = counts.sum() / (Config.num_gestures * counts)
print(f"Class weights: rest={class_weights[0]:.2f}  clench={class_weights[1]:.2f}  wrist={class_weights[2]:.2f}")
model = StudentTransformer(class_weights=class_weights)
model = model.to(device)

# Count parameters
num_params = sum(p.numel() for p in model.parameters())
print(f"Model parameters: {num_params:,}")

# Optimizer
# weight_decay adds L2 regularization: penalises large weights during training,
# pushing the model toward simpler solutions that generalise better to new data.
# without it AdamW defaults to 0 (no penalty). 0.01 is a standard starting value.
optimizer = torch.optim.AdamW(model.parameters(), lr=Config.learning_rate, weight_decay=0.01)

best_val_loss = float('inf')
best_val_acc = 0

# Training loop
print("\nStarting training...")
try:
    for epoch in range(Config.num_epochs):
        # Training
        model.train()
        train_loss = 0
        train_correct = 0
        train_total = 0

        for batch_windows, batch_labels in train_loader:
            batch_windows = batch_windows.to(device)
            batch_labels = batch_labels.to(device)

            # Forward
            logits, loss = model(batch_windows, batch_labels)

            # Backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # Track stats
            train_loss += loss.item()
            predictions = logits.argmax(dim=-1)
            train_correct += (predictions == batch_labels).sum().item()
            train_total += len(batch_labels)

        # Validation
        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for batch_windows, batch_labels in val_loader:
                batch_windows = batch_windows.to(device)
                batch_labels = batch_labels.to(device)

                logits, loss = model(batch_windows, batch_labels)

                val_loss += loss.item()
                predictions = logits.argmax(dim=-1)
                val_correct += (predictions == batch_labels).sum().item()
                val_total += len(batch_labels)

        # Calculate stats
        train_loss /= len(train_loader)
        train_acc = 100 * train_correct / train_total
        val_loss /= len(val_loader)
        val_acc = 100 * val_correct / val_total

        # Print stats
        print(f"Epoch {epoch+1}/{Config.num_epochs} | "
              f"Train Loss: {train_loss:.3f} Acc: {train_acc:.1f}% | "
              f"Val Loss: {val_loss:.3f} Acc: {val_acc:.1f}%", end="")

        # Save best model whenever val loss improves (still runs all 50 epochs)
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_val_acc = val_acc
            torch.save(model.state_dict(), os.path.join(PROJECT_ROOT, 'student_model_best.pth'))
            print(" Best!")
        else:
            print()

except KeyboardInterrupt:
    print("\n\nStopped early (Ctrl+C)")

# Save final model and print summary
torch.save(model.state_dict(), os.path.join(PROJECT_ROOT, 'student_model_final.pth'))
print(f"\nBest val loss: {best_val_loss:.3f}  |  Best val acc: {best_val_acc:.1f}%")
print("student_model_best.pth  <- best epoch during training")
print("student_model_final.pth <- weights at stop point")

# Confusion matrix on validation set using best saved model
print("\nGenerating confusion matrix...")
best_model = StudentTransformer(class_weights=class_weights).to(device)
best_model.load_state_dict(torch.load(os.path.join(PROJECT_ROOT, 'student_model_best.pth'), map_location=device))
best_model.eval()

all_preds = []
all_targets = []
with torch.no_grad():
    for batch_windows, batch_labels in val_loader:
        batch_windows = batch_windows.to(device)
        logits, _ = best_model(batch_windows, batch_labels.to(device))
        all_preds.extend(logits.argmax(dim=-1).cpu().tolist())
        all_targets.extend(batch_labels.tolist())

GESTURE_NAMES = ['rest', 'clench', 'wrist']
num_classes = len(GESTURE_NAMES)
matrix = [[0] * num_classes for _ in range(num_classes)]
for true, pred in zip(all_targets, all_preds):
    matrix[true][pred] += 1

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(matrix, cmap='Blues')
ax.set_xticks(range(num_classes))
ax.set_yticks(range(num_classes))
ax.set_xticklabels(GESTURE_NAMES)
ax.set_yticklabels(GESTURE_NAMES)
ax.set_xlabel('Predicted')
ax.set_ylabel('True')
ax.set_title(f'Confusion Matrix — Val set (best model, {best_val_acc:.1f}%)')
for i in range(num_classes):
    for j in range(num_classes):
        ax.text(j, i, matrix[i][j], ha='center', va='center',
                color='white' if matrix[i][j] > max(max(row) for row in matrix) * 0.5 else 'black')
plt.colorbar(im)
plt.tight_layout()
plt.savefig(os.path.join(PROJECT_ROOT, 'confusion_matrix.png'), dpi=150)
print("Saved confusion_matrix.png")
plt.show()