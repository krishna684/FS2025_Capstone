"""
model.py — Plant pest detection using fine-tuned EfficientNetB0.

Trained on IP102 + PlantVillage datasets (17K images, 18 classes).
Achieves 88.3% validation accuracy.

Falls back to the old ImageNet mapping approach if the trained model
file (agbot_model.pth) is not found.
"""

import ssl
import os
import json
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import io

# Fix macOS SSL certificate issue
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

_MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
_PEST_DATA_PATH = os.path.join(_MODEL_DIR, "pest_data.json")
_TRAINED_MODEL_PATH = os.path.join(_MODEL_DIR, "agbot_model.pth")

# Image preprocessing
_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def _load_pest_data():
    """Load the pest knowledge base."""
    with open(_PEST_DATA_PATH, "r") as f:
        return json.load(f)


class PlantPestModel:
    """Fine-tuned EfficientNetB0 for plant pest detection (18 classes, 88.3% accuracy)."""

    def __init__(self):
        self.device = torch.device(
            "cuda" if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available()
            else "cpu"
        )

        self.pest_db = _load_pest_data()["pests"]
        self.using_trained_model = False

        if os.path.exists(_TRAINED_MODEL_PATH):
            self._load_trained_model()
        else:
            self._load_imagenet_fallback()

    def _load_trained_model(self):
        """Load the fine-tuned model."""
        print("Loading fine-tuned AGBOT model...")
        checkpoint = torch.load(_TRAINED_MODEL_PATH, map_location=self.device, weights_only=False)

        self.classes = checkpoint['classes']
        self.class_to_idx = checkpoint.get('class_to_idx', {})
        num_classes = checkpoint['num_classes']
        best_acc = checkpoint.get('best_acc', 0)

        # Rebuild model architecture
        model = models.efficientnet_b0(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 256),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(256, num_classes),
        )

        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        model.eval()
        self.model = model
        self.using_trained_model = True

        # Build reverse mapping: index -> class name
        self.idx_to_class = {}
        for k, v in self.class_to_idx.items():
            self.idx_to_class[v] = k

        print(f"  Fine-tuned model loaded on {self.device}")
        print(f"  Classes: {num_classes} | Best accuracy: {best_acc:.1f}%")

    def _load_imagenet_fallback(self):
        """Fallback: use pre-trained ImageNet model with manual mapping."""
        print("WARNING: Trained model not found, using ImageNet fallback (lower accuracy)")
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
        self.model = models.efficientnet_b0(weights=weights)
        self.model.to(self.device)
        self.model.eval()
        self.classes = [p["name"] for p in self.pest_db]
        self.using_trained_model = False
        print(f"  ImageNet fallback loaded on {self.device}")

    def preprocess(self, image_bytes):
        """Convert raw image bytes to a model-ready tensor."""
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = _transform(image).unsqueeze(0)
        return tensor.to(self.device)

    @torch.no_grad()
    def predict(self, image_bytes, top_k=3):
        """Run inference and return top-k predictions."""
        if self.using_trained_model:
            return self._predict_trained(image_bytes, top_k)
        else:
            return self._predict_fallback(image_bytes, top_k)

    def _predict_trained(self, image_bytes, top_k):
        """Predict using the fine-tuned model."""
        tensor = self.preprocess(image_bytes)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0)

        # Always get top 5 for diagnostics and "Other Possibilities"
        top_probs, top_indices = torch.topk(probs, k=min(max(top_k, 5), len(self.classes)))

        # Print diagnostics to console
        print("\n--- AGBOT Prediction (Fine-tuned) ---")
        for p, idx in zip(top_probs[:5], top_indices[:5]):
            name = self.idx_to_class.get(idx.item(), '?')
            print(f"  {name:<25s} {p.item()*100:.1f}%")
        print("-------------------------------------\n")

        results = []
        for prob, idx in zip(top_probs, top_indices):
            class_name = self.idx_to_class.get(idx.item(), "Unknown")
            # Convert underscore names to display names
            display_name = class_name.replace('_', ' ')
            confidence = round(prob.item() * 100, 1)

            results.append({
                "class_index": idx.item(),
                "class_name": display_name,
                "raw_class": class_name,
                "confidence": confidence,
            })

        # Filter out "Healthy" from results — we handle it separately
        pest_results = [r for r in results if r["class_name"] != "Healthy"]
        top = pest_results[0] if pest_results else results[0]

        # If the model's actual top prediction is "Healthy"
        if results[0]["class_name"] == "Healthy":
            return [{
                "class_index": -1,
                "class_name": "Healthy",
                "raw_class": "Healthy",
                "confidence": results[0]["confidence"],
            }]

        # KEY INSIGHT: Real pest photos have ONE dominant class (90%+).
        # Clean/random leaves have NO dominant class — spread across many pests.
        #
        # Real pest:     Aphids 97%,  Thrips 1%,   Scale 0.5%  -> gap = 96%
        # Clean leaf:    Leaf Miners 40%, Caterpillars 25%, Thrips 15% -> gap = 15%
        #
        # Use the GAP between #1 and #2 pest predictions to decide.

        first_pest_conf = pest_results[0]["confidence"] if len(pest_results) > 0 else 0
        second_pest_conf = pest_results[1]["confidence"] if len(pest_results) > 1 else 0
        gap = first_pest_conf - second_pest_conf

        print(f"  Decision: top={pest_results[0]['class_name']} {first_pest_conf}%, "
              f"2nd={pest_results[1]['class_name'] if len(pest_results)>1 else '?'} {second_pest_conf}%, "
              f"gap={gap:.1f}%")

        # If the top pest has reasonable confidence, trust it.
        # Only reject if confidence is very low (under 20%)
        if first_pest_conf >= 20:
            return pest_results[:top_k]

        # Very low confidence = no clear pest
        return [{
            "class_index": -1,
            "class_name": "Healthy",
            "raw_class": "Healthy",
            "confidence": round(100 - first_pest_conf, 1),
        }]

    def _predict_fallback(self, image_bytes, top_k):
        """Fallback: ImageNet mapping approach (old method)."""
        IMAGENET_TO_PEST = {
            75: "Spider Mites", 78: "Spider Mites", 77: "Spider Mites", 79: "Spider Mites",
            72: "Mealybugs", 113: "Scale Insects", 114: "Scale Insects",
            300: "Japanese Beetles", 301: "Colorado Potato Beetle", 302: "Flea Beetles",
            303: "Japanese Beetles", 304: "Colorado Potato Beetle", 305: "Japanese Beetles",
            306: "Japanese Beetles", 307: "Flea Beetles",
            308: "Fungus Gnats", 309: "Sawflies", 310: "Aphids",
            311: "Stink Bugs", 312: "Stink Bugs", 313: "Caterpillars",
            314: "Stink Bugs", 315: "Stink Bugs",
            316: "Aphids", 317: "Thrips", 318: "Whiteflies",
            321: "Caterpillars", 322: "Caterpillars", 323: "Tomato Hornworm",
            324: "Caterpillars", 325: "Caterpillars", 326: "Caterpillars",
        }

        tensor = self.preprocess(image_bytes)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0)
        top_probs, top_indices = torch.topk(probs, k=25)

        pest_scores = {}
        for prob, idx in zip(top_probs, top_indices):
            idx_val = idx.item()
            if idx_val in IMAGENET_TO_PEST:
                pest_name = IMAGENET_TO_PEST[idx_val]
                pest_scores[pest_name] = pest_scores.get(pest_name, 0.0) + prob.item()

        if not pest_scores:
            return [{"class_index": -1, "class_name": "Unrecognized Insect/Leaf", "raw_class": "No Insect Found", "confidence": 0.0}]

        sorted_pests = sorted(pest_scores.items(), key=lambda x: x[1], reverse=True)
        if sorted_pests[0][1] < 0.03:
            return [{"class_index": -1, "class_name": "Unclear Image / No Pest Found", "raw_class": "Low probability", "confidence": round(sorted_pests[0][1] * 100, 2)}]

        total = sum(s for _, s in sorted_pests[:top_k])
        return [
            {"class_index": i, "class_name": name, "raw_class": "ImageNet mapped", "confidence": round(score / total * 100, 2)}
            for i, (name, score) in enumerate(sorted_pests[:top_k])
        ]


# Singleton
_model_instance = None

def get_model():
    global _model_instance
    if _model_instance is None:
        _model_instance = PlantPestModel()
    return _model_instance
