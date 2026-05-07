"""
Train MobileNetV2 model using PyTorch (works on Python 3.14)
-------------------------------------------------------------
Usage:
    python download_dataset.py   # first download images
    python train.py              # then train

Output:
    buffalo_breed_model.pth  — trained PyTorch model weights
    classes.txt              — breed names in index order
"""

import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models

# ── Config ─────────────────────────────────────────────────────────────────────
DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
MODEL_OUT   = os.path.join(os.path.dirname(__file__), "buffalo_breed_model.pth")
CLASSES_OUT = os.path.join(os.path.dirname(__file__), "classes.txt")

IMG_SIZE   = 224
BATCH_SIZE = 16
EPOCHS     = 20
LR         = 1e-3
DEVICE     = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Using device: {DEVICE}")

# ── Data ───────────────────────────────────────────────────────────────────────
train_transforms = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(20),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

val_transforms = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

def get_loaders():
    full_dataset = datasets.ImageFolder(DATASET_DIR, transform=train_transforms)
    classes = full_dataset.classes
    print(f"Found {len(classes)} classes: {classes}")

    val_size   = int(0.2 * len(full_dataset))
    train_size = len(full_dataset) - val_size
    train_ds, val_ds = random_split(full_dataset, [train_size, val_size])

    # Apply val transforms to val split
    val_ds.dataset = datasets.ImageFolder(DATASET_DIR, transform=val_transforms)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    return train_loader, val_loader, classes

# ── Model ──────────────────────────────────────────────────────────────────────
def build_model(num_classes):
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    # Freeze all layers except classifier
    for param in model.features.parameters():
        param.requires_grad = False
    # Replace classifier head
    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(model.last_channel, 256),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(256, num_classes),
    )
    return model.to(DEVICE)

# ── Train ──────────────────────────────────────────────────────────────────────
def train():
    if not os.path.exists(DATASET_DIR):
        print(f"❌ Dataset not found at {DATASET_DIR}")
        print("   Run: python download_dataset.py")
        return

    train_loader, val_loader, classes = get_loaders()
    num_classes = len(classes)

    model     = build_model(num_classes)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.classifier.parameters(), lr=LR)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)

    best_acc  = 0.0
    no_improve = 0

    print(f"\n🚀 Training for up to {EPOCHS} epochs on {DEVICE}...")
    print("-" * 50)

    for epoch in range(1, EPOCHS + 1):
        # ── Training phase ──
        model.train()
        running_loss = 0.0
        correct = 0
        total   = 0

        for imgs, labels in train_loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss    = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * imgs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total   += labels.size(0)

        train_loss = running_loss / total
        train_acc  = correct / total * 100

        # ── Validation phase ──
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total   = 0

        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
                outputs = model(imgs)
                loss    = criterion(outputs, labels)
                val_loss    += loss.item() * imgs.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += (preds == labels).sum().item()
                val_total   += labels.size(0)

        val_loss = val_loss / val_total
        val_acc  = val_correct / val_total * 100
        scheduler.step(val_loss)

        print(f"Epoch {epoch:02d}/{EPOCHS} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.1f}% | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.1f}%")

        # Save best model
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save({
                "model_state": model.state_dict(),
                "classes":     classes,
                "num_classes": num_classes,
            }, MODEL_OUT)
            print(f"  ✅ Best model saved (val acc: {best_acc:.1f}%)")
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= 5:
                print("  ⏹ Early stopping.")
                break

    # Save classes.txt
    with open(CLASSES_OUT, "w") as f:
        for cls in classes:
            f.write(f"{cls}\n")

    print("\n" + "=" * 50)
    print(f"✅ Training complete!")
    print(f"   Best validation accuracy: {best_acc:.1f}%")
    print(f"   Model saved: {MODEL_OUT}")
    print(f"   Classes saved: {CLASSES_OUT}")
    print("\nNext: upload buffalo_breed_model.pth to Render")

if __name__ == "__main__":
    train()
