"""
prepare_dataset.py — Combine IP102 + PlantVillage datasets into a unified training set.

Maps source classes to AGBOT's pest categories + healthy + disease classes.
Creates a clean dataset/ folder with train/ and val/ splits.
"""

import os
import shutil
import random
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
IP102_DIR = BASE_DIR / "IP102-Dataset" / "classification"
PV_DIR = BASE_DIR / "plantvillage dataset" / "color"
OUTPUT_DIR = BASE_DIR / "dataset"

# Mapping: IP102 folder index → our class name
# IP102 uses 0-indexed folders (0-101), classes.txt is 1-indexed
IP102_MAP = {
    # Aphids
    24: "Aphids",          # aphids
    27: "Aphids",          # english grain aphid
    28: "Aphids",          # green bug
    29: "Aphids",          # bird cherry-oat aphid
    89: "Aphids",          # Toxoptera citricidus
    90: "Aphids",          # Toxoptera aurantii
    91: "Aphids",          # Aphis citricola

    # Caterpillars
    1: "Caterpillars",     # rice leaf caterpillar
    18: "Caterpillars",    # black cutworm
    19: "Caterpillars",    # large cutworm
    20: "Caterpillars",    # yellow cutworm
    23: "Caterpillars",    # army worm
    38: "Caterpillars",    # cabbage army worm
    39: "Caterpillars",    # beet army worm
    86: "Caterpillars",    # Prodenia litura

    # Whiteflies
    71: "Whiteflies",      # Trialeurodes vaporariorum
    82: "Whiteflies",      # Aleurocanthus spiniferus

    # Spider Mites
    21: "Spider_Mites",    # red spider
    32: "Spider_Mites",    # longlegged spider mite
    74: "Spider_Mites",    # Panonchus citri McGregor

    # Thrips
    12: "Thrips",          # grain spreader thrips
    33: "Thrips",          # wheat phloeothrips
    54: "Thrips",          # Thrips
    92: "Thrips",          # Scirtothrips dorsalis Hood

    # Flea Beetles
    37: "Flea_Beetles",    # flea beetle

    # Sawflies
    34: "Sawflies",        # wheat sawfly

    # Scale Insects
    77: "Scale_Insects",   # Icerya purchasi Maskell
    78: "Scale_Insects",   # Ceroplastes rubens
    79: "Scale_Insects",   # Chrysomphalus aonidum
    80: "Scale_Insects",   # Parlatoria zizyphus

    # Mealybugs
    64: "Mealybugs",       # Pseudococcus comstocki Kuwana
    81: "Mealybugs",       # Nipaecoccus vastalor

    # Leaf Miners
    35: "Leaf_Miners",     # cerodonta denticornis
    88: "Leaf_Miners",     # Phyllocnistis citrella Stainton

    # Stink Bugs
    47: "Stink_Bugs",      # tarnished plant bug
    57: "Stink_Bugs",      # Apolygus lucorum
    70: "Stink_Bugs",      # Miridae

    # Beetles (Japanese Beetles, Colorado Potato Beetle)
    25: "Japanese_Beetles",    # Potosiabre vitarsis
    43: "Japanese_Beetles",    # sericaorient alismots chulsky
    62: "Colorado_Potato_Beetle",  # oides decempunctata

    # Fungus Gnats (closest available)
    36: "Fungus_Gnats",    # beet fly
    40: "Fungus_Gnats",    # Beet spot flies

    # Tomato Hornworm (large caterpillars/moths)
    17: "Tomato_Hornworm", # white margined moth
    41: "Tomato_Hornworm", # meadow moth
    66: "Tomato_Hornworm", # Ampelophaga
}

# PlantVillage → our class name
PV_MAP = {
    # Healthy leaves (combine all healthy classes)
    "Apple___healthy": "Healthy",
    "Blueberry___healthy": "Healthy",
    "Cherry_(including_sour)___healthy": "Healthy",
    "Corn_(maize)___healthy": "Healthy",
    "Grape___healthy": "Healthy",
    "Peach___healthy": "Healthy",
    "Pepper,_bell___healthy": "Healthy",
    "Potato___healthy": "Healthy",
    "Raspberry___healthy": "Healthy",
    "Soybean___healthy": "Healthy",
    "Strawberry___healthy": "Healthy",
    "Tomato___healthy": "Healthy",

    # Disease classes from PlantVillage
    "Apple___Apple_scab": "Leaf_Disease",
    "Apple___Black_rot": "Leaf_Disease",
    "Apple___Cedar_apple_rust": "Leaf_Disease",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": "Leaf_Disease",
    "Corn_(maize)___Common_rust_": "Leaf_Disease",
    "Corn_(maize)___Northern_Leaf_Blight": "Leaf_Disease",
    "Grape___Black_rot": "Leaf_Disease",
    "Grape___Esca_(Black_Measles)": "Leaf_Disease",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "Leaf_Disease",
    "Potato___Early_blight": "Leaf_Disease",
    "Potato___Late_blight": "Leaf_Disease",
    "Tomato___Bacterial_spot": "Leaf_Disease",
    "Tomato___Early_blight": "Leaf_Disease",
    "Tomato___Late_blight": "Leaf_Disease",
    "Tomato___Leaf_Mold": "Leaf_Disease",
    "Tomato___Septoria_leaf_spot": "Leaf_Disease",
    "Tomato___Target_Spot": "Leaf_Disease",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "Leaf_Disease",
    "Tomato___Tomato_mosaic_virus": "Leaf_Disease",

    # Spider mites from PlantVillage
    "Tomato___Spider_mites Two-spotted_spider_mite": "Spider_Mites",

    # Powdery mildew
    "Cherry_(including_sour)___Powdery_mildew": "Powdery_Mildew",
    "Squash___Powdery_mildew": "Powdery_Mildew",

    # Other
    "Orange___Haunglongbing_(Citrus_greening)": "Leaf_Disease",
    "Peach___Bacterial_spot": "Leaf_Disease",
    "Pepper,_bell___Bacterial_spot": "Leaf_Disease",
    "Strawberry___Leaf_scorch": "Leaf_Disease",
}

# Our final class list
CLASSES = [
    "Healthy",
    "Aphids",
    "Whiteflies",
    "Spider_Mites",
    "Caterpillars",
    "Mealybugs",
    "Thrips",
    "Scale_Insects",
    "Leaf_Miners",
    "Japanese_Beetles",
    "Fungus_Gnats",
    "Tomato_Hornworm",
    "Colorado_Potato_Beetle",
    "Flea_Beetles",
    "Sawflies",
    "Stink_Bugs",
    "Leaf_Disease",
    "Powdery_Mildew",
]

MAX_PER_CLASS = 1500  # Cap per class to balance dataset
VAL_RATIO = 0.15      # 15% validation split


def copy_images(src_dir, dst_dir, max_count=None):
    """Copy images from src to dst, return count."""
    os.makedirs(dst_dir, exist_ok=True)
    images = [f for f in os.listdir(src_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))]
    if max_count:
        random.shuffle(images)
        images = images[:max_count]
    for img in images:
        src = os.path.join(src_dir, img)
        # Add prefix to avoid filename collisions
        dst = os.path.join(dst_dir, f"{Path(src_dir).name}_{img}")
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
    return len(images)


def main():
    random.seed(42)

    # Clean output
    if OUTPUT_DIR.exists():
        print(f"Removing existing {OUTPUT_DIR}...")
        shutil.rmtree(OUTPUT_DIR)

    print("=" * 60)
    print("AGBOT Dataset Preparation")
    print("=" * 60)

    # Collect all images per class
    class_images = {c: [] for c in CLASSES}

    # Process IP102
    print("\n--- Processing IP102 Dataset ---")
    for folder_idx, our_class in IP102_MAP.items():
        src = IP102_DIR / "train" / str(folder_idx)
        if not src.exists():
            print(f"  SKIP: IP102 folder {folder_idx} not found")
            continue
        images = [src / f for f in os.listdir(src) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        class_images[our_class].extend(images)
        # Also grab val images
        val_src = IP102_DIR / "val" / str(folder_idx)
        if val_src.exists():
            images = [val_src / f for f in os.listdir(val_src) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            class_images[our_class].extend(images)
        print(f"  {our_class} <- IP102/{folder_idx}: {len(class_images[our_class])} total")

    # Process PlantVillage
    print("\n--- Processing PlantVillage Dataset ---")
    for pv_class, our_class in PV_MAP.items():
        src = PV_DIR / pv_class
        if not src.exists():
            print(f"  SKIP: PlantVillage '{pv_class}' not found")
            continue
        images = [src / f for f in os.listdir(src) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        class_images[our_class].extend(images)
        print(f"  {our_class} <- PV/{pv_class}: +{len(images)}")

    # Create train/val splits
    print("\n--- Creating Train/Val Splits ---")
    print(f"{'Class':<25} {'Total':>7} {'Train':>7} {'Val':>7}")
    print("-" * 50)

    total_train = 0
    total_val = 0

    for cls in CLASSES:
        images = class_images[cls]
        random.shuffle(images)

        # Cap at MAX_PER_CLASS
        if len(images) > MAX_PER_CLASS:
            images = images[:MAX_PER_CLASS]

        if len(images) < 10:
            print(f"  {cls:<25} {'SKIPPED (< 10 images)':>7}")
            continue

        # Split
        val_count = max(int(len(images) * VAL_RATIO), 5)
        val_images = images[:val_count]
        train_images = images[val_count:]

        # Copy to output
        train_dir = OUTPUT_DIR / "train" / cls
        val_dir = OUTPUT_DIR / "val" / cls
        os.makedirs(train_dir, exist_ok=True)
        os.makedirs(val_dir, exist_ok=True)

        for img_path in train_images:
            dst = train_dir / f"{img_path.parent.name}_{img_path.name}"
            shutil.copy2(img_path, dst)

        for img_path in val_images:
            dst = val_dir / f"{img_path.parent.name}_{img_path.name}"
            shutil.copy2(img_path, dst)

        total_train += len(train_images)
        total_val += len(val_images)
        print(f"  {cls:<25} {len(images):>7} {len(train_images):>7} {len(val_images):>7}")

    print("-" * 50)
    print(f"  {'TOTAL':<25} {total_train+total_val:>7} {total_train:>7} {total_val:>7}")

    # Save class list
    classes_file = OUTPUT_DIR / "classes.txt"
    active_classes = [c for c in CLASSES if (OUTPUT_DIR / "train" / c).exists()]
    with open(classes_file, 'w') as f:
        for i, cls in enumerate(active_classes):
            f.write(f"{i}\t{cls}\n")
    print(f"\nSaved {len(active_classes)} classes to {classes_file}")
    print(f"Dataset ready at: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
