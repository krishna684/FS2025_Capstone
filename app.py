from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import random
import base64
import io
from PIL import Image
import json
import os
import sys
from werkzeug.utils import secure_filename
from models import db, User, Scan, Feedback, PestDatabase
from sqlalchemy.exc import IntegrityError

# Add ml_model to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml_model'))
from model import get_model
from knowledge_base import get_pest_info_by_name, get_all_pest_names

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-jwt-secret-key'  # Change in production

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load translations
translations = {}
for lang in ['en', 'es', 'hi', 'sw']:
    try:
        with open(f'translations/{lang}.json', 'r', encoding='utf-8') as f:
            translations[lang] = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Translation file for {lang} not found")
        translations[lang] = {}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper function for translations
def get_translation(key, lang='en'):
    keys = key.split('.')
    value = translations.get(lang, translations['en'])
    for k in keys:
        value = value.get(k, key)
    return value

# Context processor to inject language and translations into all templates
@app.context_processor
def inject_translations():
    # Get language from user settings, session, or default to 'en'
    if current_user.is_authenticated and current_user.language:
        lang = current_user.language
    else:
        lang = session.get('language', request.args.get('lang', 'en'))

    # Ensure lang is valid
    if not lang or lang not in translations:
        lang = 'en'

    # Get translations for the current language
    trans = translations.get(lang, translations['en'])

    # Create a simple namespace object for dot notation access
    class TranslationNamespace:
        def __init__(self, data):
            for key, value in data.items():
                if isinstance(value, dict):
                    setattr(self, key, TranslationNamespace(value))
                else:
                    setattr(self, key, value)

        def __getattr__(self, name):
            # Return empty string for missing attributes instead of raising error
            return ''

    t = TranslationNamespace(trans)

    return dict(lang=lang, t=t)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Mock data storage (in production, use a database)
scan_history = []
user_data = {
    'name': 'Farmer',
    'location': 'Wireframe',
    'total_scans': 247,
    'healthy_percentage': 89,
    'pests_detected': 12,
    'ai_accuracy': 94,
    'model_accuracy': 94.2,
    'inference_time': 0.8
}

# Sample pest data
recent_detections = [
    {
        'id': 1,
        'pest': 'Japanese Beetle',
        'crop': 'Soybean Leaf',
        'field': 'Field A',
        'severity': 'High',
        'percentage': 93,
        'date': '2025-11-12',
        'time': '14:30'
    },
    {
        'id': 2,
        'pest': 'Aphid Colony',
        'crop': 'Corn Leaf',
        'field': 'Field B',
        'severity': 'Moderate',
        'percentage': 87,
        'date': '2025-11-11',
        'time': '09:15'
    },
    {
        'id': 3,
        'pest': 'No Pest Detected',
        'crop': 'Tomato Leaf',
        'field': 'Field C',
        'severity': 'Healthy',
        'percentage': 96,
        'date': '2025-11-10',
        'time': '16:45'
    }
]

# Pest detection trends data
pest_trends = {
    'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    'values': [12, 7, 14, 21, 18, 23]
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # Get language from query parameter and store in session
    if request.args.get('lang'):
        session['language'] = request.args.get('lang')

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter((User.email == email) | (User.phone == email)).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Invalid email/phone or password', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # Get language from query parameter and store in session
    if request.args.get('lang'):
        session['language'] = request.args.get('lang')

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        raw_phone = request.form.get('phone', '').strip()
        phone = raw_phone or None  # empty string -> None
        location = request.form.get('location')
        password = request.form.get('password')

        # Check if user exists by email
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        # Check if user exists by phone (if provided)
        if phone and User.query.filter_by(phone=phone).first():
            flash('Phone number already registered', 'danger')
            return redirect(url_for('register'))

        # Create new user
        user = User(name=name, email=email, phone=phone, location=location)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Email or phone is already in use.', 'danger')
            return redirect(url_for('register'))

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_user.name = request.form.get('name')
    current_user.phone = request.form.get('phone')
    current_user.location = request.form.get('location')
    current_user.farm_name = request.form.get('farm_name')
    current_user.farm_size = request.form.get('farm_size')

    # Handle crops as comma-separated values
    crops = request.form.getlist('crops')
    current_user.crops = ','.join(crops) if crops else None

    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/update_preferences', methods=['POST'])
@login_required
def update_preferences():
    current_user.language = request.form.get('language')
    current_user.units = request.form.get('units')
    current_user.theme = request.form.get('theme')
    db.session.commit()
    flash('Preferences updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/api/update_theme', methods=['POST'])
@login_required
def update_theme():
    data = request.get_json()
    theme = data.get('theme', 'light')
    current_user.theme = theme
    db.session.commit()
    return jsonify({'message': 'Theme updated successfully'}), 200

@app.route('/api/update_language', methods=['POST'])
@login_required
def update_language():
    data = request.get_json()
    language = data.get('language', 'en')
    current_user.language = language
    db.session.commit()
    return jsonify({'message': 'Language updated successfully'}), 200

@app.route('/update_notifications', methods=['POST'])
@login_required
def update_notifications():
    # Email notifications - convert checkbox presence to boolean
    current_user.notification_email = 'email_notifications' in request.form
    current_user.notification_push = 'push_notifications' in request.form
    db.session.commit()
    flash('Notification preferences updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/update_security', methods=['POST'])
@login_required
def update_security():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_new_password')

    # Verify current password
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('settings'))

    # Verify new passwords match
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('settings'))

    # Update password
    current_user.set_password(new_password)
    db.session.commit()
    flash('Password updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/forgot_password')
def forgot_password():
    # Placeholder for password reset functionality
    return render_template('login.html')

@app.route('/oauth_login/<provider>')
def oauth_login(provider):
    # Placeholder for OAuth login
    flash(f'{provider.capitalize()} OAuth not yet configured', 'warning')
    return redirect(url_for('login'))

# API endpoint for feedback
@app.route('/api/feedback', methods=['POST'])
@login_required
def submit_feedback():
    data = request.get_json()

    feedback = Feedback(
        user_id=current_user.id,
        scan_id=data.get('scan_id'),
        is_correct=data.get('is_correct'),
        actual_pest_name=data.get('actual_pest_name'),
        notes=data.get('notes')
    )

    db.session.add(feedback)
    db.session.commit()

    return jsonify({'message': 'Feedback saved successfully'}), 200

# Get common pests for feedback dropdown
@app.route('/api/pests')
def get_pests():
    lang = request.args.get('lang', 'en')
    pests = PestDatabase.query.all()
    return jsonify([pest.to_dict(lang) for pest in pests])

# Export API endpoints
@app.route('/api/export/scans')
@login_required
def export_scans():
    scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).all()
    scans_data = [scan.to_dict() for scan in scans]

    export_format = request.args.get('format', 'json')

    if export_format == 'json':
        return jsonify(scans_data)
    elif export_format == 'csv':
        # For CSV, we'll return JSON and let the frontend handle it
        return jsonify(scans_data)
    else:
        return jsonify({'error': 'Unsupported format'}), 400

@app.route('/api/export/profile')
@login_required
def export_profile():
    profile_data = {
        'user': current_user.to_dict(),
        'total_scans': Scan.query.filter_by(user_id=current_user.id).count(),
        'exported_at': datetime.utcnow().isoformat()
    }
    return jsonify(profile_data)

@app.route('/')
@login_required
def index():
    # Calculate weekly change
    weekly_change = '+12% this week'
    monthly_change = '+5% vs last month'
    
    # Weather data
    weather = {
        'temperature': 24,
        'condition': 'Sunny',
        'humidity': 65
    }
    
    # Plant health distribution
    health_distribution = {
        'healthy': 85,
        'pest_damage': 8,
        'disease': 5,
        'critical': 2
    }
    
    return render_template('index.html', 
                         user_data=user_data,
                         recent_detections=recent_detections[:3],
                         pest_trends=pest_trends,
                         weekly_change=weekly_change,
                         monthly_change=monthly_change,
                         weather=weather,
                         health_distribution=health_distribution,
                         current_date=datetime.now().strftime('%A, %B %d, %Y'))

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/describe')
@login_required
def describe():
    return render_template('describe.html')

@app.route('/analyze_symptoms', methods=['POST'])
@login_required
def analyze_symptoms():
    """Analyze plant symptoms from text description"""
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', '').strip()
        plant_type = data.get('plant_type', '').strip()

        if not symptoms:
            return jsonify({'error': 'Please describe the symptoms'}), 400

        # AI analysis
        analysis_result = analyze_text_symptoms(symptoms, plant_type)

        # Store in database
        scan = Scan(
            user_id=current_user.id,
            pest_name=analysis_result['disease_name'],
            confidence=analysis_result['confidence'],
            severity=analysis_result.get('severity', 'Unknown'),
            scan_type='text_description'
        )
        db.session.add(scan)
        db.session.commit()

        # Store for results page
        session['last_analysis'] = analysis_result

        return jsonify({'success': True, 'redirect': url_for('results')})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_text_symptoms(symptoms, plant_type=''):
    """AI-powered symptom analysis using real pest knowledge base."""
    symptoms_lower = symptoms.lower()

    # Match against the real pest knowledge base (15 species)
    all_pest_names = get_all_pest_names()
    kb_matches = []

    for pest_name in all_pest_names:
        pest_info = get_pest_info_by_name(pest_name)
        if not pest_info:
            continue
        score = 0
        for symptom in pest_info.get('symptoms', []):
            for word in symptom.lower().split():
                if len(word) > 3 and word in symptoms_lower:
                    score += 1
        if pest_name.lower() in symptoms_lower:
            score += 5
        if plant_type:
            for plant in pest_info.get('affected_plants', []):
                if plant_type.lower() in plant.lower() or plant.lower() in plant_type.lower():
                    score += 2
        if score > 0:
            kb_matches.append((score, pest_info))

    # Also check disease-specific keywords
    diseases = [
        {'name': 'Powdery Mildew', 'scientific': 'Erysiphales', 'keywords': ['white', 'powder', 'dusty', 'coating', 'mildew'], 'description': 'White powdery coating on leaves and stems', 'causes': ['High humidity', 'Poor air circulation', 'Overhead watering'], 'severity': 'Moderate', 'chemical': ['Sulfur-based fungicide', 'Potassium bicarbonate spray'], 'organic': ['Baking soda solution (1 tbsp per gallon water)', 'Milk spray (1:10 ratio)', 'Neem oil'], 'prevention': ['Improve air circulation', 'Water at base only', 'Remove infected leaves']},
        {'name': 'Leaf Blight', 'scientific': 'Alternaria spp.', 'keywords': ['brown', 'spots', 'yellow', 'halo', 'target', 'ring'], 'description': 'Brown spots with yellow halos on leaves', 'causes': ['Fungal infection', 'Water splash', 'High humidity'], 'severity': 'High', 'chemical': ['Copper fungicide', 'Chlorothalonil'], 'organic': ['Remove infected leaves', 'Compost tea spray', 'Improve drainage'], 'prevention': ['Crop rotation', 'Drip irrigation', 'Remove debris']},
        {'name': 'Early Blight', 'scientific': 'Alternaria solani', 'keywords': ['dark', 'concentric', 'circles', 'lower leaves', 'bulls'], 'description': 'Dark spots with concentric rings, typically on lower leaves', 'causes': ['Soil-borne fungus', 'Warm humid weather', 'Water splash'], 'severity': 'High', 'chemical': ['Copper fungicide', 'Mancozeb'], 'organic': ['Remove affected leaves', 'Mulch heavily', 'Baking soda spray'], 'prevention': ['3-year crop rotation', 'Stake plants', 'Water at soil level']},
        {'name': 'Nutrient Deficiency', 'scientific': 'N/A', 'keywords': ['yellow', 'pale', 'chlorosis', 'stunted', 'discolor'], 'description': 'Yellowing or pale leaves, stunted growth', 'causes': ['Poor soil nutrition', 'pH imbalance', 'Nutrient lockout'], 'severity': 'Mild', 'chemical': ['NPK fertilizer', 'Chelated iron'], 'organic': ['Compost', 'Fish emulsion', 'Seaweed extract', 'pH adjustment'], 'prevention': ['Regular soil testing', 'Balanced fertilization', 'Proper pH maintenance']},
    ]

    disease_scores = []
    for disease in diseases:
        matches = sum(1 for kw in disease['keywords'] if kw in symptoms_lower)
        if matches > 0:
            disease_scores.append((matches, disease))

    # Use KB match if stronger
    if kb_matches:
        kb_matches.sort(reverse=True, key=lambda x: x[0])
        best_kb = kb_matches[0]
        best_disease_score = disease_scores[0][0] if disease_scores else 0
        if best_kb[0] >= best_disease_score:
            pest = best_kb[1]
            confidence = min(60 + (best_kb[0] * 5), 95)
            remedies = pest.get('remedies', [])
            return {
                'disease_name': pest['name'],
                'scientific_name': pest.get('scientific_name', ''),
                'confidence': confidence,
                'description': pest.get('description', ''),
                'causes': pest.get('symptoms', [])[:3],
                'severity': pest.get('severity_level', 'Unknown'),
                'chemical_treatments': [r for r in remedies if any(w in r.lower() for w in ['insecticide', 'miticide', 'fungicide', 'carbaryl', 'pyrethrin', 'systemic'])],
                'organic_treatments': [r for r in remedies if any(w in r.lower() for w in ['neem', 'soap', 'water', 'hand-pick', 'ladybug', 'diatomaceous', 'predatory'])],
                'prevention': pest.get('precautions', [])[:4],
                'user_symptoms': symptoms,
                'plant_type': plant_type
            }

    # Fallback to disease keyword matching
    if disease_scores:
        disease_scores.sort(reverse=True, key=lambda x: x[0])
        match = disease_scores[0][1]
        confidence = min(65 + (disease_scores[0][0] * 7), 94)
    else:
        match = {'name': 'General Plant Stress', 'scientific': 'Unknown', 'description': 'Unable to identify specific disease from description', 'causes': ['Environmental stress', 'Cultural issues', 'Multiple factors'], 'severity': 'Unknown', 'chemical': ['Consult agricultural extension office'], 'organic': ['Improve general care', 'Check watering', 'Inspect closely'], 'prevention': ['Regular monitoring', 'Good cultural practices']}
        confidence = 45

    return {
        'disease_name': match['name'],
        'scientific_name': match.get('scientific', ''),
        'confidence': confidence,
        'description': match['description'],
        'causes': match.get('causes', []),
        'severity': match.get('severity', 'Unknown'),
        'chemical_treatments': match.get('chemical', []),
        'organic_treatments': match.get('organic', []),
        'prevention': match.get('prevention', []),
        'user_symptoms': symptoms,
        'plant_type': plant_type
    }

@app.route('/history')
def history():
    # Get scan history with sample data
    history_data = [
        {
            'plant': 'Rose Bush',
            'pest': 'Japanese Beetle',
            'date': '2025-11-03',
            'time': '14:30',
            'severity': 'Moderate'
        },
        {
            'plant': 'Tomato Plant',
            'pest': 'Aphids',
            'date': '2025-11-01',
            'time': '09:15',
            'severity': 'Mild'
        },
        {
            'plant': 'Cabbage',
            'pest': 'Cabbage Worm',
            'date': '2025-10-30',
            'time': '16:45',
            'severity': 'Moderate'
        },
        {
            'plant': 'Bean Plant',
            'pest': 'Spider Mites',
            'date': '2025-10-28',
            'time': '11:20',
            'severity': 'Severe'
        },
        {
            'plant': 'Lettuce',
            'pest': 'None Detected',
            'date': '2025-10-25',
            'time': '13:00',
            'severity': 'Healthy'
        }
    ]
    
    stats = {
        'total_scans': 12,
        'pests_found': 8,
        'healthy': 4
    }
    
    return render_template('history.html', history=history_data, stats=stats)

@app.route('/help')
@login_required
def help_page():
    return render_template('help.html')

@app.route('/about')
def about():
    team = [
        {'name': 'Dhanya Boyapally', 'role': 'Computer Vision & ML Researcher', 'type': 'Computer'},
        {'name': 'Krishna Karra', 'role': 'Backend & Frontend Developer', 'type': 'Backend'},
        {'name': 'Jack Frater', 'role': 'Frontend & UI/UX Designer', 'type': 'Frontend'},
        {'name': 'Biao Wang', 'role': 'Machine Learning & AI Specialist', 'type': 'Machine'}
    ]
    
    return render_template('about.html', team=team)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle image upload and real AI analysis"""
    try:
        image_bytes = None

        # Check if file was uploaded
        if 'image' not in request.files:
            # Check if base64 image was sent
            json_data = request.get_json(silent=True)
            if json_data and 'image_data' in json_data:
                image_data = json_data['image_data']
                image_str = image_data.split(',')[1] if ',' in image_data else image_data
                image_bytes = base64.b64decode(image_str)
            else:
                return jsonify({'error': 'No image provided'}), 400
        else:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                with open(filepath, 'rb') as f:
                    image_bytes = f.read()
            else:
                return jsonify({'error': 'Invalid file format'}), 400

        # Run real AI model inference
        analysis_result = run_pest_detection(image_bytes)

        # Save a copy as latest_scan.jpg for the results page
        from PIL import Image as PILImage
        img = PILImage.open(io.BytesIO(image_bytes)).convert('RGB')
        latest_path = os.path.join(app.config['UPLOAD_FOLDER'], 'latest_scan.jpg')
        img.save(latest_path, 'JPEG', quality=85)

        # Store in history
        scan_history.append({
            'timestamp': datetime.now().isoformat(),
            'result': analysis_result
        })

        # Store result in session for the results page
        session['last_scan_result'] = analysis_result

        return jsonify(analysis_result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def results():
    """Display analysis results"""
    # Check for text-based analysis first
    if 'last_analysis' in session:
        analysis = session.get('last_analysis')
        latest_result = {
            'type': 'text',
            'status': 'Analyzed',
            'pest_identified': analysis['disease_name'],
            'pest_scientific': analysis.get('scientific_name', ''),
            'confidence': analysis['confidence'],
            'damage_pattern': analysis.get('description', ''),
            'severity': analysis.get('severity', 'Unknown'),
            'causes': analysis.get('causes', []),
            'chemical_treatments': analysis.get('chemical_treatments', []),
            'organic_treatments': analysis.get('organic_treatments', []),
            'prevention': analysis.get('prevention', []),
            'user_symptoms': analysis.get('user_symptoms', ''),
            'plant_type': analysis.get('plant_type', '')
        }
        session.pop('last_analysis', None)
    # Check for image scan result
    elif 'last_scan_result' in session:
        latest_result = session.get('last_scan_result')
        latest_result['type'] = 'image'
        session.pop('last_scan_result', None)
    elif scan_history:
        latest_result = scan_history[-1]['result']
        latest_result['type'] = 'image'
    else:
        latest_result = {
            'type': 'image',
            'status': 'Healthy',
            'pest_identified': 'None',
            'confidence': 0,
            'message': 'No scan performed yet. Go to Scan to analyze a plant.'
        }

    # Add cache-busting timestamp for image
    import time
    image_timestamp = int(time.time())

    return render_template('results.html', result=latest_result,
                         image_timestamp=image_timestamp,
                         timestamp=datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p'))

def run_pest_detection(image_bytes):
    """Run real EfficientNetB0 AI model inference on image bytes."""
    model = get_model()
    predictions = model.predict(image_bytes, top_k=3)

    top = predictions[0]

    # No pest detected
    if top['class_name'] in ('Unrecognized Insect/Leaf', 'Unclear Image / No Pest Found'):
        return {
            'status': 'Healthy',
            'pest_identified': 'None',
            'confidence': round(top.get('confidence', 0), 1),
            'message': 'Your plant appears to be healthy! No pests detected.',
            'severity': 'Healthy'
        }

    # Pest detected — get full info from knowledge base
    pest_info = get_pest_info_by_name(top['class_name'])

    severity = pest_info.get('severity_level', 'Unknown')
    severity_map = {'Low': 'Mild', 'Moderate': 'Moderate', 'High': 'High',
                    'Moderate to High': 'High', 'Low to Moderate': 'Moderate'}
    app_severity = severity_map.get(severity, severity)

    remedies = pest_info.get('remedies', []) or []
    precautions = pest_info.get('precautions', []) or []

    return {
        'status': 'Pest Detected',
        'pest_identified': top['class_name'],
        'pest_scientific': pest_info.get('scientific_name', ''),
        'confidence': round(top['confidence'], 1),
        'damage_pattern': pest_info.get('description', ''),
        'severity': app_severity,
        'immediate_action': app_severity in ('Moderate', 'High', 'Severe'),
        'symptoms': pest_info.get('symptoms', []),
        'affected_plants': pest_info.get('affected_plants', []),
        'treatments': {
            'immediate': remedies[:3],
            'ipm': precautions[:3],
            'prevention': precautions[3:6]
        },
        'chemical_treatments': [r for r in remedies if any(w in r.lower() for w in ['insecticide', 'miticide', 'fungicide', 'carbaryl', 'pyrethrin', 'permethrin', 'systemic', 'sulfur'])],
        'organic_treatments': [r for r in remedies if any(w in r.lower() for w in ['neem', 'soap', 'water', 'hand-pick', 'ladybug', 'diatomaceous', 'bt ', 'bacillus', 'predatory', 'companion'])],
        'all_predictions': [
            {'pest': p['class_name'], 'confidence': round(p['confidence'], 1)}
            for p in predictions if p.get('confidence', 0) > 0.1
        ]
    }

@app.route('/api/stats')
def get_stats():
    """API endpoint for dashboard statistics"""
    return jsonify({
        'total_scans': user_data['total_scans'],
        'healthy_percentage': user_data['healthy_percentage'],
        'pests_detected': user_data['pests_detected'],
        'ai_accuracy': user_data['ai_accuracy'],
        'recent_detections': recent_detections[:5],
        'pest_trends': pest_trends
    })

if __name__ == '__main__':
    # Initialize database
    with app.app_context():
        db.create_all()

        # Add sample pests if database is empty
        if PestDatabase.query.count() == 0:
            pests = [
                PestDatabase(
                    common_name='Japanese Beetle',
                    scientific_name='Popillia japonica',
                    category='insect',
                    name_es='Escarabajo Japonés',
                    name_hi='जापानी बीटल',
                    name_sw='Mdudu wa Kijapani'
                ),
                PestDatabase(
                    common_name='Aphids',
                    scientific_name='Aphidoidea',
                    category='insect',
                    name_es='Pulgones',
                    name_hi='एफिड्स',
                    name_sw='Dudu wa Majani'
                ),
                PestDatabase(
                    common_name='Spider Mites',
                    scientific_name='Tetranychidae',
                    category='insect',
                    name_es='Ácaros',
                    name_hi='मकड़ी के कण',
                    name_sw='Panya wa Utando'
                ),
                PestDatabase(
                    common_name='Cabbage Worm',
                    scientific_name='Pieris rapae',
                    category='insect',
                    name_es='Gusano de la col',
                    name_hi='पत्ता गोभी का कीड़ा',
                    name_sw='Funza la Kabichi'
                ),
                PestDatabase(
                    common_name='Whiteflies',
                    scientific_name='Aleyrodidae',
                    category='insect',
                    name_es='Moscas blancas',
                    name_hi='सफेद मक्खियाँ',
                    name_sw='Nzi Weupe'
                ),
            ]
            db.session.add_all(pests)
            db.session.commit()
            print("Database initialized with sample pests")

    # Pre-load the AI model at startup
    print("\n  Loading AI Model...")
    get_model()

    print("\n  AGBOT Web Server (AI-Powered)")
    print("  ─────────────────────────────")
    print("  Running on http://0.0.0.0:5001")
    print("  AI Model: EfficientNetB0 (PyTorch)")
    print("  Pest Database: 15 species\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
