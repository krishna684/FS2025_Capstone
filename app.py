from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from datetime import datetime, timedelta
from functools import wraps
import jwt
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
from knowledge_base import get_pest_info_by_name, get_all_pest_names, _load as _load_pest_data_raw

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-jwt-secret-key'  # Change in production

# Initialize extensions
db.init_app(app)
CORS(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Mobile API JWT config
JWT_SECRET = 'your-jwt-secret-key'  # Change in production

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

scan_history = []


def get_web_dashboard_data(user_id):
    """Build real dashboard data from the database for the web app."""
    from sqlalchemy import extract

    total_scans = Scan.query.filter_by(user_id=user_id).count()
    healthy_scans = Scan.query.filter_by(user_id=user_id, severity='Healthy').count()
    pest_scans = total_scans - healthy_scans
    healthy_pct = round((healthy_scans / total_scans * 100) if total_scans > 0 else 0)

    user_data = {
        'total_scans': total_scans,
        'healthy_percentage': healthy_pct,
        'pests_detected': pest_scans,
        'ai_accuracy': 88,
        'model_accuracy': 88.3,
        'inference_time': 0.5
    }

    recent = Scan.query.filter_by(user_id=user_id).order_by(Scan.created_at.desc()).limit(5).all()
    recent_detections = [{
        'id': s.id,
        'pest': s.pest_identified or 'Unknown',
        'crop': s.crop_type or 'Plant',
        'field': s.field_name or 'Field',
        'severity': s.severity or 'Unknown',
        'percentage': round(s.confidence or 0),
        'date': s.created_at.strftime('%Y-%m-%d') if s.created_at else '',
        'time': s.created_at.strftime('%H:%M') if s.created_at else ''
    } for s in recent]

    now = datetime.now()
    months, values = [], []
    for i in range(5, -1, -1):
        m = now.month - i
        y = now.year
        if m <= 0:
            m += 12; y -= 1
        months.append(datetime(y, m, 1).strftime('%b'))
        values.append(Scan.query.filter_by(user_id=user_id).filter(
            extract('month', Scan.created_at) == m,
            extract('year', Scan.created_at) == y
        ).count())
    pest_trends = {'months': months, 'values': values}

    if total_scans > 0:
        mild = Scan.query.filter_by(user_id=user_id, severity='Mild').count()
        moderate = Scan.query.filter_by(user_id=user_id, severity='Moderate').count()
        high = Scan.query.filter_by(user_id=user_id).filter(Scan.severity.in_(['High', 'Severe'])).count()
        health_distribution = {
            'healthy': round(healthy_scans / total_scans * 100),
            'pest_damage': round((mild + moderate) / total_scans * 100),
            'disease': round(high / total_scans * 100),
            'critical': round(Scan.query.filter_by(user_id=user_id, severity='Severe').count() / total_scans * 100),
        }
    else:
        health_distribution = {'healthy': 0, 'pest_damage': 0, 'disease': 0, 'critical': 0}

    return user_data, recent_detections, pest_trends, health_distribution


# Legacy sample detections (only shown if user has zero scans)
_sample_detections = [
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

        # Auto-login and redirect to onboarding
        login_user(user)
        return redirect(url_for('onboarding'))

    return render_template('register.html')

# /api/chat moved to api.py blueprint (hybrid auth: works for web session + mobile JWT)

@app.route('/onboarding')
@login_required
def onboarding():
    return render_template('onboarding.html')

@app.route('/chat_page')
@login_required
def chat_page():
    return render_template('chat.html')

@app.route('/pest_library')
@login_required
def pest_library():
    pest_data = _load_pest_data_raw()
    pests = pest_data.get('pests', [])
    # Add disease entries
    pests.append({'id': 100, 'name': 'Leaf Disease', 'scientific_name': 'Various pathogens', 'description': 'Leaf diseases caused by fungi, bacteria, or viruses.', 'severity_level': 'High', 'affected_plants': ['Tomatoes', 'Potatoes', 'Grapes', 'Apples', 'Corn'], 'symptoms': ['Brown or black spots', 'Yellowing around spots', 'Premature leaf drop', 'Wilting'], 'precautions': ['Crop rotation', 'Disease-resistant varieties', 'Water at soil level', 'Space plants properly'], 'remedies': ['Copper-based fungicide', 'Remove infected leaves', 'Neem oil spray', 'Improve circulation']})
    pests.append({'id': 101, 'name': 'Powdery Mildew', 'scientific_name': 'Erysiphales', 'description': 'Fungal disease causing white powdery coating on leaves.', 'severity_level': 'Moderate', 'affected_plants': ['Squash', 'Cucumbers', 'Roses', 'Grapes', 'Cherries'], 'symptoms': ['White powdery spots', 'Curling leaves', 'Stunted growth', 'Reduced fruit quality'], 'precautions': ['Improve air circulation', 'Water at base only', 'Remove infected leaves', 'Avoid overcrowding'], 'remedies': ['Sulfur-based fungicide', 'Baking soda solution', 'Neem oil spray', 'Milk spray (1:10 ratio)']})
    return render_template('pest_library.html', pests=pests)

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

# /api/update_theme and /api/update_language moved to api.py blueprint (hybrid auth)

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

# /api/feedback, /api/pests, /api/export/scans, /api/export/profile moved to api.py blueprint

@app.route('/')
@login_required
def index():
    user_data, recent_detections, pest_trends, health_distribution = get_web_dashboard_data(current_user.id)

    weather = {'temperature': 24, 'condition': 'Sunny', 'humidity': 65}

    return render_template('index.html',
                         user_data=user_data,
                         recent_detections=recent_detections[:3],
                         pest_trends=pest_trends,
                         weekly_change='',
                         monthly_change='',
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
            pest_identified=analysis_result['disease_name'],
            confidence=analysis_result['confidence'],
            severity=analysis_result.get('severity', 'Unknown'),
            status='Analyzed'
        )
        db.session.add(scan)
        db.session.commit()

        # Store for results page
        analysis_result['scan_id'] = scan.id
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
@login_required
def history():
    db_scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).all()
    history_data = []
    for scan in db_scans:
        s_dict = scan.to_dict()
        s_dict['plant'] = scan.crop_type or 'Unknown Plant'
        s_dict['pest'] = scan.pest_identified or 'None'
        if scan.created_at:
            s_dict['date'] = scan.created_at.strftime('%Y-%m-%d')
            s_dict['time'] = scan.created_at.strftime('%H:%M')
        else:
            s_dict['date'] = ''
            s_dict['time'] = ''
        history_data.append(s_dict)

    total = len(history_data)
    pests = sum(1 for h in history_data if h.get('severity') not in ['Healthy', None])
    healthy = total - pests

    stats = {
        'total_scans': total,
        'pests_found': pests,
        'healthy': healthy
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
@login_required
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

        # Save image
        from PIL import Image as PILImage
        img = PILImage.open(io.BytesIO(image_bytes)).convert('RGB')
        saved_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_scan.jpg"
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_filename), 'JPEG', quality=85)
        # Also save as latest_scan.jpg for the results page display
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], 'latest_scan.jpg'), 'JPEG', quality=85)

        # Save to database
        scan = Scan(
            user_id=current_user.id,
            image_path=saved_filename,
            pest_identified=analysis_result.get('pest_identified'),
            pest_scientific=analysis_result.get('pest_scientific', ''),
            confidence=analysis_result.get('confidence'),
            status=analysis_result.get('status'),
            severity=analysis_result.get('severity', 'Unknown'),
            damage_pattern=analysis_result.get('damage_pattern', '')
        )
        db.session.add(scan)
        db.session.commit()
        analysis_result['scan_id'] = scan.id

        # Store result in session for the results page
        session['last_scan_result'] = analysis_result

        return jsonify(analysis_result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/results')
@login_required
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

    # Healthy or no pest detected
    if top['class_name'] in ('Healthy', 'Unrecognized Insect/Leaf', 'Unclear Image / No Pest Found'):
        return {
            'status': 'Healthy',
            'pest_identified': 'None',
            'confidence': round(top.get('confidence', 0), 1),
            'message': 'Your plant appears to be healthy! No pests detected.',
            'severity': 'Healthy'
        }

    # Disease classes
    if top['class_name'] in ('Leaf Disease', 'Powdery Mildew'):
        disease_info = {
            'Leaf Disease': {
                'description': 'Leaf disease detected — signs of fungal, bacterial, or viral infection.',
                'severity': 'High',
                'remedies': ['Remove and destroy infected leaves', 'Apply copper-based fungicide', 'Improve air circulation', 'Avoid overhead watering', 'Apply neem oil spray every 7 days'],
                'precautions': ['Practice crop rotation', 'Use disease-resistant varieties', 'Water at soil level', 'Space plants properly', 'Remove plant debris at end of season'],
            },
            'Powdery Mildew': {
                'description': 'Powdery mildew detected — white powdery coating on leaves.',
                'severity': 'Moderate',
                'remedies': ['Apply sulfur-based fungicide', 'Spray baking soda solution', 'Use neem oil spray', 'Apply potassium bicarbonate', 'Use milk spray (1:10 ratio)'],
                'precautions': ['Improve air circulation', 'Water at base only', 'Remove infected leaves', 'Avoid overcrowding', 'Choose resistant varieties'],
            }
        }
        info = disease_info[top['class_name']]
        return {
            'status': 'Disease Detected',
            'pest_identified': top['class_name'],
            'pest_scientific': '',
            'confidence': round(top['confidence'], 1),
            'damage_pattern': info['description'],
            'severity': info['severity'],
            'immediate_action': True,
            'treatments': {
                'immediate': info['remedies'][:3],
                'ipm': info['precautions'][:3],
                'prevention': info['precautions'][3:6]
            },
            'chemical_treatments': [r for r in info['remedies'] if any(w in r.lower() for w in ['fungicide', 'sulfur', 'bicarbonate'])],
            'organic_treatments': [r for r in info['remedies'] if any(w in r.lower() for w in ['neem', 'baking soda', 'milk', 'remove'])],
            'all_predictions': [
                {'pest': p['class_name'], 'confidence': round(p['confidence'], 1)}
                for p in predictions if p.get('confidence', 0) > 0.1
            ]
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

# /api/stats moved to api.py blueprint (hybrid auth)


# Register the mobile API blueprint (provides /api/auth/*, /api/dashboard, /api/analyze, etc.)
from api import bp as mobile_api_bp
app.register_blueprint(mobile_api_bp)


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
    print("  Running on http://0.0.0.0:5002")
    print("  AI Model: EfficientNetB0 Fine-tuned (88.3%)")
    print("  Pest Database: 18 classes\n")
    port = int(os.environ.get('PORT', 5002))
    app.run(debug=False, host='0.0.0.0', port=port)
