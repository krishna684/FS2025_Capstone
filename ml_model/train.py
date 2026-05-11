"""
train.py — Fine-tune EfficientNetB0 on the AGBOT pest dataset.

Two-phase training:
  Phase 1: Train only the classifier head (frozen backbone) — fast convergence
  Phase 2: Unfreeze last layers and fine-tune end-to-end — higher accuracy

Usage:
    python3 ml_model/train.py
"""

import os
import sys
import time
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms, models, datasets
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "dataset"
MODEL_SAVE_PATH = BASE_DIR / "ml_model" / "agbot_model.pth"
CLASSES_PATH = DATASET_DIR / "classes.txt"

BATCH_SIZE = 32
IMAGE_SIZE = 224
NUM_WORKERS = 0  # macOS compatibility

# Phase 1: Classifier head only
PHASE1_EPOCHS = 5
PHASE1_LR = 0.001

# Phase 2: Full fine-tune
PHASE2_EPOCHS = 10
PHASE2_LR = 0.0001


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_classes():
    classes = []
    with open(CLASSES_PATH, 'r') as f:
        for line in f:
            idx, name = line.strip().split('\t')
            classes.append(name)
    return classes


def get_transforms():
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(p=0.2),
        transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.1),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    return train_transform, val_transform


def build_model(num_classes, device):
    print("Loading pre-trained EfficientNetB0...")
    weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
    model = models.efficientnet_b0(weights=weights)

    # Replace classifier head
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(p=0.2),
        nn.Linear(256, num_classes),
    )

    return model.to(device)


def freeze_backbone(model):
    """Freeze all layers except the classifier head."""
    for param in model.features.parameters():
        param.requires_grad = False
    for param in model.classifier.parameters():
        param.requires_grad = True


def unfreeze_last_layers(model, num_blocks=3):
    """Unfreeze the last N blocks of EfficientNet for fine-tuning."""
    total_blocks = len(model.features)
    for i, block in enumerate(model.features):
        if i >= total_blocks - num_blocks:
            for param in block.parameters():
                param.requires_grad = True
        else:
            for param in block.parameters():
                param.requires_grad = False
    for param in model.classifier.parameters():
        param.requires_grad = True


def train_one_epoch(model, loader, criterion, optimizer, device, epoch, total_epochs):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (images, labels) in enumerate(loader):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

        if (batch_idx + 1) % 20 == 0 or (batch_idx + 1) == len(loader):
            acc = 100. * correct / total
            avg_loss = running_loss / (batch_idx + 1)
            done = int(30 * (batch_idx + 1) / len(loader))
            bar = '#' * done + '-' * (30 - done)
            sys.stdout.write(f"\r  Epoch {epoch}/{total_epochs} [{bar}] {batch_idx+1}/{len(loader)} | Loss: {avg_loss:.4f} | Acc: {acc:.1f}%")
            sys.stdout.flush()

    avg_loss = running_loss / len(loader)
    accuracy = 100. * correct / total
    print()
    return avg_loss, accuracy


@torch.no_grad()
def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    avg_loss = running_loss / len(loader)
    accuracy = 100. * correct / total
    return avg_loss, accuracy


@torch.no_grad()
def print_per_class_accuracy(model, loader, classes, device):
    model.eval()
    class_correct = [0] * len(classes)
    class_total = [0] * len(classes)

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        _, predicted = outputs.max(1)
        for i in range(labels.size(0)):
            label = labels[i].item()
            class_total[label] += 1
            if predicted[i].item() == label:
                class_correct[label] += 1

    print(f"  {'Class':<25} {'Correct':>8} {'Total':>8} {'Accuracy':>10}")
    print(f"  {'-'*55}")
    for i, cls in enumerate(classes):
        if class_total[i] > 0:
            acc = 100. * class_correct[i] / class_total[i]
            print(f"  {cls:<25} {class_correct[i]:>8} {class_total[i]:>8} {acc:>9.1f}%")


def main():
    device = get_device()
    print(f"\n{'='*60}")
    print(f"  AGBOT Model Fine-Tuning")
    print(f"  Device: {device}")
    print(f"{'='*60}\n")

    classes = load_classes()
    num_classes = len(classes)
    print(f"Classes ({num_classes}): {', '.join(classes)}")

    train_transform, val_transform = get_transforms()
    train_dataset = datasets.ImageFolder(DATASET_DIR / "train", transform=train_transform)
    val_dataset = datasets.ImageFolder(DATASET_DIR / "val", transform=val_transform)

    print(f"Train: {len(train_dataset)} images")
    print(f"Val:   {len(val_dataset)} images")
    print(f"Detected classes: {train_dataset.classes}")

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS, pin_memory=True)

    model = build_model(num_classes, device)
    criterion = nn.CrossEntropyLoss()
    best_acc = 0.0
    all_results = []

    # ═══════════════════════════════════════════════════════════
    # Phase 1: Train classifier head only (backbone frozen)
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'_'*60}")
    print(f"  PHASE 1: Classifier Head Training ({PHASE1_EPOCHS} epochs)")
    print(f"  Learning Rate: {PHASE1_LR}")
    print(f"  Frozen: All backbone layers")
    print(f"{'_'*60}")

    freeze_backbone(model)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Trainable params: {trainable:,} / {total_params:,} ({100*trainable/total_params:.1f}%)\n")

    optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=PHASE1_LR)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=2)

    for epoch in range(1, PHASE1_EPOCHS + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device, epoch, PHASE1_EPOCHS)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        elapsed = time.time() - t0
        scheduler.step(val_acc)

        lr = optimizer.param_groups[0]['lr']
        result = {
            'phase': 1, 'epoch': epoch,
            'train_loss': round(train_loss, 4), 'val_loss': round(val_loss, 4),
            'val_acc': round(val_acc, 2), 'lr': lr, 'time': round(elapsed, 1)
        }
        all_results.append(result)

        print(f"  --> Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.1f}% | Time: {elapsed:.0f}s | LR: {lr}")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save({
                'model_state_dict': model.state_dict(),
                'classes': classes,
                'class_to_idx': train_dataset.class_to_idx,
                'num_classes': num_classes,
                'best_acc': best_acc,
                'phase': 1,
            }, MODEL_SAVE_PATH)
            print(f"  ** Saved best model (Phase 1): {best_acc:.1f}% **")

    # ═══════════════════════════════════════════════════════════
    # Phase 2: Fine-tune full model (unfreeze last layers)
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'_'*60}")
    print(f"  PHASE 2: Full Fine-Tuning ({PHASE2_EPOCHS} epochs)")
    print(f"  Learning Rate: {PHASE2_LR}")
    print(f"  Unfreezing last 3 backbone blocks")
    print(f"{'_'*60}")

    unfreeze_last_layers(model, num_blocks=3)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Trainable params: {trainable:,} / {total_params:,} ({100*trainable/total_params:.1f}%)\n")

    optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=PHASE2_LR)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=2)

    for epoch in range(1, PHASE2_EPOCHS + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device, epoch, PHASE2_EPOCHS)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        elapsed = time.time() - t0
        scheduler.step(val_acc)

        lr = optimizer.param_groups[0]['lr']
        result = {
            'phase': 2, 'epoch': epoch,
            'train_loss': round(train_loss, 4), 'val_loss': round(val_loss, 4),
            'val_acc': round(val_acc, 2), 'lr': lr, 'time': round(elapsed, 1)
        }
        all_results.append(result)

        print(f"  --> Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.1f}% | Time: {elapsed:.0f}s | LR: {lr}")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save({
                'model_state_dict': model.state_dict(),
                'classes': classes,
                'class_to_idx': train_dataset.class_to_idx,
                'num_classes': num_classes,
                'best_acc': best_acc,
                'phase': 2,
            }, MODEL_SAVE_PATH)
            print(f"  ** Saved best model (Phase 2): {best_acc:.1f}% **")

    # ═══════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════
    model_size = MODEL_SAVE_PATH.stat().st_size / 1024 / 1024

    print(f"\n{'='*60}")
    print(f"  TRAINING COMPLETE")
    print(f"  Best Validation Accuracy: {best_acc:.1f}%")
    print(f"  Model saved to: {MODEL_SAVE_PATH}")
    print(f"  Model size: {model_size:.1f} MB")
    print(f"{'='*60}")

    # Save training log
    log_path = BASE_DIR / "ml_model" / "training_log.json"
    log_data = {
        'device': str(device),
        'num_classes': num_classes,
        'classes': classes,
        'best_accuracy': best_acc,
        'total_train_images': len(train_dataset),
        'total_val_images': len(val_dataset),
        'results': all_results,
    }
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    print(f"  Training log saved to: {log_path}\n")

    print("Per-class validation accuracy:")
    print_per_class_accuracy(model, val_loader, classes, device)


if __name__ == "__main__":
    main()
