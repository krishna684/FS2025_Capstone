# AGBOT - AI-Powered Plant Pest Detection

Agricultural pest detection system powered by EfficientNetB0 (PyTorch). Available as a web app, React Native mobile app (iOS/Android), and native SwiftUI iOS app.

## Project Structure

```
agbot_app/
├── app.py                 # Flask web app (HTML templates)
├── api.py                 # REST API for mobile apps (JSON)
├── models.py              # SQLAlchemy database models
├── ml_model/              # AI model & pest knowledge base
│   ├── model.py           # EfficientNetB0 inference
│   ├── knowledge_base.py  # Pest info lookup
│   ├── questionnaire.py   # Rule-based pest identification
│   ├── pest_data.json     # 15 pest species data
│   └── questionnaire_data.json
├── mobile/                # React Native (Expo) mobile app
│   ├── App.js
│   ├── src/
│   │   ├── screens/       # All app screens
│   │   ├── services/      # API client
│   │   ├── context/       # Auth, Theme, Language providers
│   │   └── navigation/    # Stack + Tab navigation
│   └── package.json
├── ios/AGBOT/             # Native SwiftUI iOS app
│   ├── AGBOTApp.swift     # App entry point
│   ├── Models/            # Codable data models
│   ├── Services/          # API + Auth services
│   ├── Views/             # All SwiftUI screens
│   ├── Theme/             # Light/dark theme
│   └── Translations/      # Multilingual support
├── templates/             # Web app HTML templates
├── translations/          # Multilingual JSON (en, es, hi, sw)
└── instance/agbot.db      # SQLite database (auto-created)
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- Expo Go app on your phone (for React Native)
- Xcode 15+ (for native iOS only)

### 1. Clone & Setup

```bash
git clone <repo-url>
cd agbot_app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install flask flask-cors flask-login flask-sqlalchemy PyJWT Pillow werkzeug torch torchvision python-multipart
```

### 2. Run the Web App

```bash
python3 app.py
```
Open http://localhost:5001 in your browser.

### 3. Test on Mobile (React Native / Expo)

#### Step 1: Find your computer's IP address

```bash
# macOS
ipconfig getifaddr en0

# Linux
hostname -I | awk '{print $1}'

# Windows
ipconfig | findstr IPv4
```

#### Step 2: Update the API URL in the mobile app

Open `mobile/src/services/api.js` and change line 4:
```javascript
const BASE_URL = 'http://YOUR_IP_HERE:5001';
```

#### Step 3: Start the API server (not the web app)

```bash
python3 api.py
```

> **Important:** `app.py` and `api.py` both use port 5001. Only run one at a time.
> - `app.py` = web app (HTML pages)
> - `api.py` = mobile API (JSON responses)

#### Step 4: Start the Expo dev server

```bash
cd mobile
npm install
npx expo start
```

#### Step 5: Open on your phone

1. Install **Expo Go** from the App Store / Play Store
2. Make sure your phone is on the **same WiFi network** as your computer
3. Scan the QR code shown in the terminal
4. The app will load in Expo Go

#### Troubleshooting

| Problem | Solution |
|---|---|
| "Network request failed" | Your IP changed. Run `ipconfig getifaddr en0` and update `api.js` |
| Expo Go version mismatch | Update Expo Go from App Store, or run `npx expo start --tunnel` |
| "Connection refused" | Make sure `python3 api.py` is running |
| Scanning hangs forever | Check terminal for errors. Restart `api.py` |
| Port 5001 in use | Kill it: `lsof -ti:5001 \| xargs kill -9` |

### 4. Test Native iOS App (SwiftUI)

1. Keep `python3 api.py` running
2. Open **Xcode** > File > New > Project > iOS App (SwiftUI, Swift)
3. Name it `AGBOT`
4. Delete the auto-generated `ContentView.swift`
5. Drag all files from `ios/AGBOT/` into the Xcode project
6. Update the IP in `ios/AGBOT/Services/APIService.swift` line 21
7. Build and run (iOS 16+)

## Features

- AI-powered pest detection using EfficientNetB0 (15 pest species)
- Camera capture and photo gallery upload
- Text-based symptom analysis
- Scan history with expandable details
- User feedback on AI accuracy
- Dark/light theme
- Multilingual (English, Spanish, Hindi, Swahili)
- Real-time dashboard with scan stats and charts

## Database

SQLite database (`instance/agbot.db`) with 4 tables:
- **users** - Authentication & profile
- **scans** - Scan history & results
- **feedbacks** - User corrections on AI results
- **pests** - Reference pest data

The database is auto-created on first run. Each developer gets their own local copy.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/register` | Register |
| GET | `/api/dashboard` | Dashboard data |
| POST | `/api/analyze` | Scan image (multipart) |
| POST | `/api/analyze_symptoms` | Text symptom analysis |
| GET | `/api/history` | Scan history |
| POST | `/api/chat` | Pest Q&A chatbot |
| PUT | `/api/profile` | Update profile |
| PUT | `/api/security` | Change password |
| GET | `/api/health` | Health check |

## Team

- Dhanya Boyapally - Computer Vision & ML Researcher
- Krishna Karra - Backend & Frontend Developer
- Jack Frater - Frontend & UI/UX Designer
- Biao Wang - Machine Learning & AI Specialist
