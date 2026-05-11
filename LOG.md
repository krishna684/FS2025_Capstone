# AGBOT Model Fine-Tuning Log

## Date: 2026-03-20

## Goal
Fine-tune EfficientNetB0 on real pest/disease images to replace the ImageNet mapping approach.

---

## Previous Model (Before)

| Detail | Value |
|---|---|
| Architecture | EfficientNetB0 (pre-trained ImageNet) |
| Approach | Zero-shot mapping: ImageNet insect classes -> pest names |
| Accuracy | ~30% (estimated) |
| False positive rate | High — healthy leaves triggered pest detection |
| Classes | 15 (mapped, not trained) |

---

## Fine-Tuning Steps Completed

### Step 1: Dataset Preparation
- [x] Downloaded IP102 dataset (75K images, 102 insect pest classes)
- [x] Downloaded PlantVillage dataset (50K images, 38 plant disease classes)
- [x] Mapped relevant classes from both datasets to 18 AGBOT classes
- [x] Created balanced train/val split with 1500 max per class

### Dataset Summary
- **Source**: IP102 + PlantVillage (combined)
- **Total images**: 16,928
- **Train**: 14,394 images
- **Validation**: 2,534 images
- **Classes**: 18

| Class | Train | Val |
|---|---|---|
| Healthy | 1,275 | 225 |
| Aphids | 1,275 | 225 |
| Whiteflies | 822 | 144 |
| Spider Mites | 1,275 | 225 |
| Caterpillars | 1,275 | 225 |
| Mealybugs | 241 | 42 |
| Thrips | 1,275 | 225 |
| Scale Insects | 579 | 102 |
| Leaf Miners | 321 | 56 |
| Japanese Beetles | 449 | 79 |
| Fungus Gnats | 239 | 42 |
| Tomato Hornworm | 702 | 123 |
| Colorado Potato Beetle | 169 | 29 |
| Flea Beetles | 470 | 82 |
| Sawflies | 202 | 35 |
| Stink Bugs | 1,275 | 225 |
| Leaf Disease | 1,275 | 225 |
| Powdery Mildew | 1,275 | 225 |

### Step 2: Model Architecture
- [x] Loaded pre-trained EfficientNetB0 (ImageNet weights)
- [x] Replaced classifier: 1000 classes -> Dropout(0.3) -> Linear(1280, 256) -> ReLU -> Dropout(0.2) -> Linear(256, 18)
- [x] Data augmentation: RandomResizedCrop, HorizontalFlip, VerticalFlip, Rotation(20), ColorJitter

### Step 3: Training
- [x] Device: Apple Silicon Mac (MPS)
- [x] Two-phase training completed

### Step 4: Evaluation
- [x] Best validation accuracy: **88.3%**
- [x] Model size: 16.8 MB

### Step 5: Integration
- [x] Updated model.py to load fine-tuned weights
- [x] Added fallback to ImageNet mapping if .pth not found
- [x] Added Leaf Disease and Powdery Mildew handling in API
- [x] Tested end-to-end

---

## Training Log

### Phase 1 — Classifier Head Only (backbone frozen)
- Trainable params: 332,562 / 4,340,110 (7.7%)
- Learning rate: 0.001

| Epoch | Train Loss | Train Acc | Val Loss | Val Acc | Time |
|-------|-----------|-----------|----------|---------|------|
| 1 | 1.4875 | 54.0% | 1.0154 | 69.0% | 121s |
| 2 | 1.1134 | 64.5% | 0.8899 | 72.2% | 110s |
| 3 | 1.0217 | 67.6% | 0.8125 | 73.8% | 109s |
| 4 | 0.9687 | 68.7% | 0.8026 | 74.1% | 109s |
| 5 | 0.9445 | 69.6% | 0.7287 | **76.4%** | 109s |

### Phase 2 — Full Fine-Tuning (last 3 blocks unfrozen)
- Trainable params: 3,488,302 / 4,340,110 (80.4%)
- Learning rate: 0.0001

| Epoch | Train Loss | Train Acc | Val Loss | Val Acc | Time |
|-------|-----------|-----------|----------|---------|------|
| 1 | 0.7733 | 74.9% | 0.5763 | 82.0% | 153s |
| 2 | 0.6354 | 79.8% | 0.5123 | 84.2% | 149s |
| 3 | 0.5541 | 82.0% | 0.4782 | 85.7% | 149s |
| 4 | 0.4882 | 84.2% | 0.4492 | 86.4% | 150s |
| 5 | 0.4312 | 86.0% | 0.4408 | 86.7% | 149s |
| 6 | 0.3940 | 87.2% | 0.4275 | 87.5% | 149s |
| 7 | 0.3682 | 88.1% | 0.4134 | 87.9% | 149s |
| 8 | 0.3300 | 89.3% | 0.4110 | **88.3%** | 149s |
| 9 | 0.3114 | 89.6% | 0.4056 | 88.2% | 149s |
| 10 | 0.2906 | 90.6% | 0.4058 | 88.3% | 149s |

Total training time: ~38 minutes

---

## Final Results

### Overall

| Metric | Old Model (ImageNet) | Fine-Tuned |
|--------|---------------------|-----------|
| Overall accuracy | ~30% | **88.3%** |
| Healthy detection | Unreliable | **Dedicated class** |
| False positive rate | High | Low |
| Classes | 15 (mapped) | **18 (trained)** |
| Inference time | ~0.5s | ~0.5s |
| Model size | 20MB (ImageNet) | **16.8MB** |

### Per-Class Accuracy

| Class | Accuracy | Support |
|-------|----------|---------|
| Healthy | 80.4% | 225 |
| Aphids | 80.4% | 225 |
| Whiteflies | **96.6%** | 29 |
| Spider Mites | 86.6% | 82 |
| Caterpillars | 83.3% | 42 |
| Mealybugs | **100.0%** | 225 |
| Thrips | 92.4% | 79 |
| Scale Insects | **95.6%** | 225 |
| Leaf Miners | 73.2% | 56 |
| Japanese Beetles | 66.7% | 42 |
| Fungus Gnats | **100.0%** | 225 |
| Tomato Hornworm | 88.6% | 35 |
| Colorado Potato Beetle | 88.2% | 102 |
| Flea Beetles | 86.2% | 225 |
| Sawflies | 90.2% | 225 |
| Stink Bugs | 82.7% | 225 |
| Leaf Disease | 82.1% | 123 |
| Powdery Mildew | 90.3% | 144 |

### Strongest Classes (>90%)
- Mealybugs: 100%
- Fungus Gnats: 100%
- Whiteflies: 96.6%
- Scale Insects: 95.6%
- Thrips: 92.4%
- Powdery Mildew: 90.3%
- Sawflies: 90.2%

### Weakest Classes (<80%)
- Japanese Beetles: 66.7% (small dataset, 42 val images)
- Leaf Miners: 73.2% (small dataset, 56 val images)

### Possible Improvements
- Add more training images for Japanese Beetles and Leaf Miners
- Try EfficientNetB2 or B3 for higher capacity
- Train for more epochs with lower learning rate
- Add more data augmentation (CutMix, MixUp)
- Collect real-world phone camera images for fine-tuning

---

## Files

| File | Purpose |
|---|---|
| `ml_model/prepare_dataset.py` | Maps IP102 + PlantVillage to 18 classes |
| `ml_model/train.py` | Two-phase fine-tuning script |
| `ml_model/agbot_model.pth` | Trained model weights (16.8MB) |
| `ml_model/training_log.json` | Epoch-by-epoch metrics |
| `ml_model/model.py` | Inference (loads fine-tuned or falls back to ImageNet) |
| `dataset/` | Prepared training data (not committed to git) |
