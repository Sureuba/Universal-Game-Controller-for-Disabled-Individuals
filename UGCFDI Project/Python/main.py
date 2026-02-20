import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from csv_loader import load_csv_data_split
from student_transformer import StudentTransformer
from config import Config

# Device selection
device = 'cuda' if torch.cuda.is_available() else 'cpu'   #if gpu is there probably better
print(f"Using device: {device}")

# Load data (uses Config defaults)
print("\nLoading data...")
train_windows, train_labels, val_windows, val_labels = load_csv_data_split('data')

# Create dataloaders
train_dataset = TensorDataset(train_windows, train_labels)
val_dataset = TensorDataset(val_windows, val_labels)

train_loader = DataLoader(train_dataset, batch_size=Config.batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=Config.batch_size, shuffle=False)

# Create model (uses Config defaults)
print("\nCreating model...")
model = StudentTransformer()  # All defaults from Config
model = model.to(device)

# Count parameters
num_params = sum(p.numel() for p in model.parameters())
print(f"Model parameters: {num_params:,}")

# Optimizer
optimizer = torch.optim.AdamW(model.parameters(), lr=Config.learning_rate)

# Early stopping
best_val_loss = float('inf')
best_val_acc = 0
patience_counter = 0

# Training loop
print("\nStarting training...")
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
    
    # Early stopping
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        best_val_acc = val_acc
        patience_counter = 0
        torch.save(model.state_dict(), 'student_model_best.pth')
        print(" Best!")
    else:
        patience_counter += 1
        print()
        if patience_counter >= Config.patience:
            print(f"\nEarly stopping at epoch {epoch+1}")
            print(f"Best val loss: {best_val_loss:.3f}")
            print(f"Best val acc: {best_val_acc:.1f}%")
            break

# Save final model
torch.save(model.state_dict(), 'student_model_final.pth')
print(f"\nTraining complete!")
print(f"Best validation accuracy: {best_val_acc:.1f}%")
print("Best model saved to: student_model_best.pth")
print("Final model saved to: student_model_final.pth")