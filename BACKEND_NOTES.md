# AGBOT Backend Architecture — Demo Walkthrough

## System Overview

```
                         ┌─────────────┐
                         │   Frontend   │
                         ├──────┬──────┤
                         │ Web  │Mobile│
                         │(HTML)│(Expo)│
                         └──┬───┴──┬───┘
                            │      │
                    ┌───────┘      └───────┐
                    ▼                      ▼
              ┌───────────┐         ┌───────────┐
              │  app.py   │         │  api.py   │
              │Flask-Login│         │  JWT Auth │
              │ (Sessions)│         │  (Tokens) │
              └─────┬─────┘         └─────┬─────┘
                    │                     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌────────────┐  ┌────────────┐  ┌──────────────┐
       │  models.py │  │  model.py  │  │knowledge_base│
       │ SQLAlchemy │  │EfficientNet│  │  pest_data   │
       │   (ORM)    │  │   B0 AI    │  │   (JSON)     │
       └──────┬─────┘  └────────────┘  └──────────────┘
              │
              ▼
       ┌────────────┐
       │  agbot.db  │
       │  (SQLite)  │
       └────────────┘
```

---

## 1. Database Layer (models.py)

**4 tables** in SQLite (`instance/agbot.db`):

### Users Table
```
users
├── id            (PRIMARY KEY)
├── email         (UNIQUE, indexed)
├── phone         (UNIQUE)
├── password_hash (bcrypt via Werkzeug)
├── name, location, language, theme
├── farm_name, farm_size, crops
├── notification_email, notification_push
├── created_at, last_login, is_active
└── oauth_provider, oauth_id (future SSO)
```

### Scans Table
```
scans
├── id            (PRIMARY KEY)
├── user_id       (FK → users, CASCADE DELETE)
├── image_path    (saved in static/uploads/)
├── pest_identified, pest_scientific
├── confidence    (float 0-100)
├── status        ('Healthy' | 'Pest Detected' | 'Disease Detected')
├── severity      ('Healthy' | 'Mild' | 'Moderate' | 'High' | 'Severe')
├── crop_type, field_name
├── damage_pattern (text description)
└── created_at    (indexed for fast history queries)
```

### Feedbacks Table
```
feedbacks
├── id, user_id (FK), scan_id (FK)
├── is_correct    (boolean — was the AI right?)
├── actual_pest_name, actual_pest_scientific
├── notes, helpful
└── created_at
```
> This table is key for model improvement — we can retrain using user corrections.

### Pests Reference Table
```
pests (multilingual reference)
├── id, common_name, scientific_name, category
├── description
└── name_es, name_hi, name_sw (localized names)
```

**Demo talking point:** Relationships use CASCADE DELETE — deleting a user removes all their scans and feedback. The feedback table creates a data flywheel for model improvement.

---

## 2. AI Model Pipeline (ml_model/)

### Architecture
```
EfficientNetB0 (pretrained ImageNet → fine-tuned on pest data)
├── Backbone: 1280-dim feature extractor (partially frozen)
└── Custom Head:
    Dropout(0.3) → Linear(1280, 256) → ReLU → Dropout(0.2) → Linear(256, 18)
```

### 18 Detection Classes
| Pests (15) | Diseases (2) | Status (1) |
|------------|-------------|------------|
| Aphids | Leaf Disease | Healthy |
| Whiteflies | Powdery Mildew | |
| Spider Mites | | |
| Caterpillars | | |
| Mealybugs | | |
| Thrips | | |
| Scale Insects | | |
| Leaf Miners | | |
| Japanese Beetles | | |
| Fungus Gnats | | |
| Tomato Hornworm | | |
| Colorado Potato Beetle | | |
| Flea Beetles | | |
| Sawflies | | |
| Stink Bugs | | |

### Training Pipeline (train.py)

**Datasets used:**
- **IP102** — 102 real-world insect pest classes (75K images) → mapped to our 15 pest classes
- **PlantVillage** — 38 plant disease classes (54K images) → used for Healthy + Disease classes

**Two-Phase Training:**
```
Phase 1: Classifier Head Only (5 epochs)
  ├── Freeze all backbone layers
  ├── Train only the new classification head
  ├── Learning rate: 0.001
  ├── Trainable params: 332K / 4.3M (7.7%)
  └── Result: 76.4% validation accuracy

Phase 2: Full Fine-Tuning (10 epochs)
  ├── Unfreeze last 3 backbone blocks
  ├── Lower learning rate: 0.0001 (stability)
  ├── Trainable params: 3.5M / 4.3M (80.4%)
  └── Result: 88.3% validation accuracy
```

**Data Augmentation (training only):**
- RandomResizedCrop, HorizontalFlip, VerticalFlip
- RandomRotation(20°)
- ColorJitter (brightness, contrast, saturation, hue)

**Demo talking point:** Transfer learning lets us achieve 88% accuracy with only ~17K images and 2 hours of training on a MacBook (Apple MPS). Without transfer learning, this would need 100K+ images and GPU servers.

### Inference Pipeline
```
Photo (bytes) → PIL Image → Resize(256) → CenterCrop(224) → Normalize
     → EfficientNetB0 forward pass → Softmax → Top-3 predictions
     → Confidence thresholding → Final result + knowledge base lookup
```

**Processing time:** ~200ms on MacBook M-series, ~500ms on CPU

### Confidence Thresholding Logic
```python
# Real pest photo:  Aphids 97%, Thrips 2%, Mealybugs 1%  → HIGH confidence → Trust it
# Clean leaf photo: Miners 25%, Caterpillars 20%, Thrips 15% → LOW confidence → "Healthy"

if top_pest_confidence >= 20%:
    return pest_prediction      # Model is confident
else:
    return "Healthy"            # Model is uncertain → safer to say healthy
```

---

## 3. Knowledge Base (pest_data.json)

Each of the 15 pests has a complete profile:

```json
{
  "name": "Aphids",
  "scientific_name": "Aphidoidea",
  "severity_level": "Moderate",
  "affected_plants": ["Roses", "Tomatoes", "Peppers", ...],
  "symptoms": ["Curling leaves", "Sticky honeydew", "Black sooty mold", ...],
  "remedies": ["Insecticidal soap", "Neem oil spray", "Release ladybugs", ...],
  "precautions": ["Inspect new plants", "Encourage natural predators", ...]
}
```

**Used by:** Results page, Pest Library, Chat bot, Text symptom analysis

---

## 4. Authentication — Two Systems

### Web App (app.py) — Flask-Login Sessions
```
Register/Login → Server creates session cookie → Browser stores cookie
→ Every request: @login_required checks session → current_user available
→ Logout: Session destroyed
```

### Mobile API (api.py) — JWT Tokens
```
Register/Login → Server generates JWT (30-day expiry, HS256)
→ Client stores token in AsyncStorage
→ Every request: Authorization: Bearer <token>
→ @token_required decorator decodes token → current_user injected
```

**Why two systems?** Web browsers use cookies natively. Mobile apps need stateless tokens that can be stored locally and sent in headers.

**Password security:** Werkzeug's `generate_password_hash` / `check_password_hash` (PBKDF2-SHA256, salted)

---

## 5. API Endpoints

### Core Endpoints (api.py — mobile)
| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/auth/login` | POST | — | Email/phone + password → JWT token |
| `/api/auth/register` | POST | — | Create account → JWT token |
| `/api/dashboard` | GET | JWT | Stats, trends, recent detections, weather |
| `/api/analyze` | POST | JWT | Upload image → AI analysis → save to DB |
| `/api/analyze_symptoms` | POST | JWT | Text symptoms → keyword matching → result |
| `/api/history` | GET | JWT | All user's past scans |
| `/api/chat` | POST | JWT | Pest Q&A chatbot |
| `/api/feedback` | POST | JWT | Submit scan accuracy feedback |
| `/api/pest_library` | GET | — | Full pest encyclopedia |
| `/api/pests` | GET | — | Pest dropdown list (localized) |
| `/api/export/scans` | GET | JWT | Export all scans as JSON |
| `/api/health` | GET | — | Server status check |

### Web Routes (app.py)
| Route | Purpose |
|-------|---------|
| `/` | Dashboard (real DB data) |
| `/scan` | Camera/upload page |
| `/analyze` | Process image → AI → save → redirect to results |
| `/history` | Scan history list |
| `/chat_page` | Chat interface |
| `/pest_library` | Browse all pests |
| `/settings` | Profile, preferences, security |
| `/onboarding` | New user welcome flow |

---

## 6. Data Flow — Complete Scan Pipeline

```
1. USER taps "Scan" → Takes photo or selects from gallery

2. UPLOAD → Image sent as multipart form or base64
   → Server saves to static/uploads/TIMESTAMP_scan.jpg

3. PREPROCESS → PIL opens image → Resize(256) → CenterCrop(224)
   → Normalize with ImageNet stats → Tensor on GPU/MPS

4. AI INFERENCE → EfficientNetB0 forward pass
   → Softmax over 18 classes → Top-3 predictions

5. DECISION LOGIC → Apply confidence threshold
   → If confident: return pest name + confidence
   → If uncertain: return "Healthy"

6. KNOWLEDGE BASE LOOKUP → Match pest name to pest_data.json
   → Pull symptoms, remedies, precautions, affected plants

7. SAVE TO DB → Create Scan record
   (user_id, image_path, pest_identified, confidence, severity)

8. RESPONSE → Return full analysis result
   → Web: render results.html template
   → Mobile: JSON response
```

---

## 7. Text Symptom Analysis Pipeline

```
1. USER describes: "yellow curling leaves with sticky residue on tomato"

2. TOKENIZE → Split into words > 3 characters
   → ["yellow", "curling", "leaves", "sticky", "residue", "tomato"]

3. SCORE EACH PEST:
   Aphids:     +1(curling) +1(sticky) +5(name match) +2(tomato) = 9
   Whiteflies: +1(sticky) +1(yellow) +2(tomato) = 4
   Thrips:     +1(curling) = 1
   ...

4. ALSO CHECK DISEASES:
   Powdery Mildew: keywords=[white,powder,dusty] → 0 matches
   Leaf Blight:    keywords=[brown,spots,yellow] → 1 match

5. WINNER → Aphids (score 9) vs Leaf Blight (score 1)
   → Aphids wins
   → Confidence = min(60 + 9*5, 95) = 95%

6. RETURN → Aphids with symptoms, remedies, severity from KB
```

---

## 8. Multilingual Support

**4 languages:** English, Spanish (es), Hindi (hi), Swahili (sw)

- Translation files: `translations/{en,es,hi,sw}.json`
- Web: Jinja2 context processor injects `t` object into every template
- Mobile: `/api/translations/<lang>` endpoint returns full JSON
- Pest names: `PestDatabase.to_dict(language)` returns localized names
- User preference saved in DB (`users.language` column)

---

## 9. Key Technical Decisions

| Decision | Why |
|----------|-----|
| **EfficientNetB0** over larger models | Best accuracy/size ratio. 16.8MB model, runs on phone CPUs |
| **Two-phase training** | Phase 1 prevents catastrophic forgetting. Phase 2 adapts backbone features |
| **SQLite** over PostgreSQL | Single-file DB, zero config, perfect for demo/prototype stage |
| **Flask** over Django | Lightweight, flexible, easier to split into web + API |
| **JWT** for mobile, Sessions for web | Stateless tokens for mobile (no cookie support), sessions for web (browser-native) |
| **Feedback table** | Creates data flywheel — user corrections can retrain the model |
| **Knowledge base JSON** | Fast in-memory lookups, easy to edit, no DB query overhead |

---

## 10. Model Performance

### Training Results
| Metric | Value |
|--------|-------|
| Validation Accuracy | 88.3% |
| Model Size | 16.8 MB |
| Training Time | ~25 min (MacBook MPS) |
| Training Images | ~17,000 (IP102 + PlantVillage) |
| Classes | 18 (15 pests + 2 diseases + healthy) |

### Per-Class Accuracy (Top/Bottom)
| Best Classes | Accuracy | Hardest Classes | Accuracy |
|-------------|----------|----------------|----------|
| Mealybugs | 100% | Japanese Beetles | 66.7% |
| Fungus Gnats | 100% | Leaf Miners | 73.2% |
| Powdery Mildew | 100% | Caterpillars | 83.3% |
| Whiteflies | 96.6% | Aphids | 80.4% |
| Scale Insects | 95.6% | Healthy | 80.4% |

### Confusion Pairs (commonly mixed up)
- Leaf Miners ↔ Caterpillars (both are larvae damage)
- Mealybugs ↔ Scale Insects (visually similar)
- Scale Insects ↔ Aphids (both cluster on stems)

---

## 11. Security Measures

- Passwords: PBKDF2-SHA256 hashed (never stored in plaintext)
- JWT: HS256 signed, 30-day expiry, secret key from env or generated
- CORS: Enabled for mobile API access
- File uploads: Extension whitelist (png/jpg/jpeg/gif/webp/bmp/tiff)
- SQL injection: Prevented by SQLAlchemy ORM (parameterized queries)
- XSS: Jinja2 auto-escapes template variables
- Cascade deletes: User deletion cleans up all related data

---

## 12. Future Improvements

- **Model accuracy**: More training data, harder augmentation, ensemble models
- **Real-time chatbot**: Integrate LLM API (Claude/GPT) for contextual answers
- **Real weather API**: OpenWeatherMap integration based on user location
- **Push notifications**: Seasonal pest alerts
- **Offline mode**: Cache model on device for field use without internet
- **Feedback loop**: Auto-retrain model using user corrections from feedback table
