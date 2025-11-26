from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import random
import base64
import io
from PIL import Image
import json
import os
import logging
from werkzeug.utils import secure_filename
from config import config
from database import db, init_db, get_mongo_db, close_db_connections
from models import User, Scan, Feedback, PestDatabase, Treatment, IPMRecommendation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize database connections
init_db(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Register teardown handler for database connections
@app.teardown_appcontext
def shutdown_session(exception=None):
    close_db_connections()

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

# Helper function for translations with fallback
def get_translation(key, lang='en'):
    """
    Get translation for a key with fallback to English
    
    Args:
        key: Translation key in dot notation (e.g., 'dashboard.greeting')
        lang: Language code
        
    Returns:
        Translated string or English fallback
    """
    keys = key.split('.')
    
    # Try to get translation in requested language
    value = translations.get(lang, {})
    found = True
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            found = False
            break
    
    # If translation found and is a string, return it
    if found and isinstance(value, str):
        return value
    
    # Fall back to English
    if lang != 'en':
        value = translations.get('en', {})
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Log missing translation key
                log_missing_translation(key, lang)
                return key
        
        # Log that we're using English fallback
        if isinstance(value, str):
            log_missing_translation(key, lang)
            return value
    
    # If even English doesn't have it, return the key itself
    log_missing_translation(key, lang)
    return key


# Helper function to log missing translations
def log_missing_translation(key, language):
    """
    Log missing translation keys to file for future addition
    
    Args:
        key: Translation key that was missing
        language: Language code where translation was missing
    """
    try:
        log_file = 'missing_translations.log'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] Missing translation: key='{key}', language='{language}'\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
    except Exception as e:
        logger.error(f"Error logging missing translation: {e}")


# Helper function to get localized pest name
def get_localized_pest_name(pest_id, language='en'):
    """
    Get localized pest name from database
    
    Args:
        pest_id: ID of the pest in PestDatabase
        language: Language code ('en', 'es', 'hi', 'sw')
        
    Returns:
        Localized pest name or English name as fallback
    """
    try:
        pest = PestDatabase.query.get(pest_id)
        
        if not pest:
            logger.warning(f"Pest with id={pest_id} not found")
            return None
        
        # For English, return common_name directly
        if language == 'en':
            return pest.common_name
        
        # Query appropriate name field based on language
        name_field = f'name_{language}'
        localized_name = getattr(pest, name_field, None)
        
        # Fall back to English if localized name not available
        if not localized_name:
            logger.info(f"Localized name not found for pest_id={pest_id}, language={language}. Using English.")
            return pest.common_name
        
        return localized_name
        
    except Exception as e:
        logger.error(f"Error getting localized pest name: {e}")
        return None

# Helper function to detect browser language from Accept-Language header
def detect_browser_language():
    """
    Detect language from browser Accept-Language header
    Returns best match from supported languages or 'en' as default
    """
    # Get Accept-Language header
    accept_language = request.headers.get('Accept-Language', '')
    
    if not accept_language:
        return 'en'
    
    # Parse Accept-Language header (format: "en-US,en;q=0.9,es;q=0.8")
    # Extract language codes and their quality values
    supported_languages = ['en', 'es', 'hi', 'sw']
    
    # Split by comma to get individual language preferences
    language_preferences = []
    for lang_entry in accept_language.split(','):
        # Split by semicolon to separate language from quality value
        parts = lang_entry.strip().split(';')
        lang_code = parts[0].strip()
        
        # Extract just the language part (e.g., 'en' from 'en-US')
        if '-' in lang_code:
            lang_code = lang_code.split('-')[0]
        
        # Get quality value (default to 1.0 if not specified)
        quality = 1.0
        if len(parts) > 1 and parts[1].strip().startswith('q='):
            try:
                quality = float(parts[1].strip()[2:])
            except ValueError:
                quality = 1.0
        
        language_preferences.append((lang_code.lower(), quality))
    
    # Sort by quality value (descending)
    language_preferences.sort(key=lambda x: x[1], reverse=True)
    
    # Find first supported language
    for lang_code, _ in language_preferences:
        if lang_code in supported_languages:
            return lang_code
    
    # Default to English if no match found
    return 'en'


# Context processor to inject language and translations into all templates
@app.context_processor
def inject_translations():
    # Language detection priority: user profile > session > browser header > default 'en'
    lang = None
    
    # Priority 1: User profile language (if authenticated)
    if current_user.is_authenticated and current_user.language:
        lang = current_user.language
    
    # Priority 2: Session language
    if not lang:
        lang = session.get('language')
    
    # Priority 3: Browser Accept-Language header
    if not lang:
        lang = detect_browser_language()
    
    # Priority 4: Default to English
    if not lang:
        lang = 'en'

    # Ensure lang is valid
    if lang not in translations:
        lang = 'en'

    # Get translations for the current language
    trans = translations.get(lang, translations['en'])
    trans_en = translations.get('en', {})

    # Create a simple namespace object for dot notation access with fallback
    class TranslationNamespace:
        def __init__(self, data, fallback_data=None, current_lang='en', path=''):
            self._data = data
            self._fallback = fallback_data
            self._lang = current_lang
            self._path = path
            
            for key, value in data.items():
                fallback_value = fallback_data.get(key) if fallback_data else None
                new_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict):
                    setattr(self, key, TranslationNamespace(
                        value, 
                        fallback_value if isinstance(fallback_value, dict) else None,
                        current_lang,
                        new_path
                    ))
                else:
                    setattr(self, key, value)

        def __getattr__(self, name):
            # Check if key exists in current language
            if name.startswith('_'):
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
            
            # Try to get from fallback (English)
            if self._fallback and isinstance(self._fallback, dict) and name in self._fallback:
                fallback_value = self._fallback[name]
                new_path = f"{self._path}.{name}" if self._path else name
                
                # Log missing translation
                if self._lang != 'en':
                    log_missing_translation(new_path, self._lang)
                
                if isinstance(fallback_value, dict):
                    return TranslationNamespace(
                        fallback_value,
                        fallback_value,
                        self._lang,
                        new_path
                    )
                return fallback_value
            
            # Return empty string if not found anywhere
            return ''

    t = TranslationNamespace(trans, trans_en if lang != 'en' else None, lang)

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
        phone = request.form.get('phone')
        location = request.form.get('location')
        password = request.form.get('password')

        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        # Create new user
        user = User(name=name, email=email, phone=phone, location=location)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

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
    from db_sync import sync_feedback_to_mongodb
    
    data = request.get_json()
    scan_id = data.get('scan_id')
    is_correct = data.get('is_correct')
    actual_pest_name = data.get('actual_pest_name')
    notes = data.get('notes')
    
    # Validate scan_id exists
    scan = Scan.query.get(scan_id)
    if not scan:
        return jsonify({'error': 'Scan not found'}), 404

    # Create feedback in PostgreSQL
    feedback = Feedback(
        user_id=current_user.id,
        scan_id=scan_id,
        is_correct=is_correct,
        actual_pest_name=actual_pest_name,
        notes=notes
    )

    db.session.add(feedback)
    db.session.commit()
    
    # Get the feedback ID after commit
    feedback_id = feedback.id
    
    # Update scan status if incorrect
    if not is_correct:
        scan.status = 'corrected'
        db.session.commit()
    
    # Sync to MongoDB asynchronously
    sync_feedback_to_mongodb(
        feedback_id=feedback_id,
        detection_id=scan_id,
        user_id=current_user.id,
        is_correct=is_correct,
        corrected_label=actual_pest_name,
        confidence_in_correction='high' if not is_correct else None,
        comments=notes,
        image_flagged_for_retraining=(not is_correct)
    )

    return jsonify({'message': 'Feedback saved successfully'}), 200


# API endpoint for feedback aggregation (admin/system use)
@app.route('/api/admin/feedback/aggregate', methods=['GET'])
@login_required
def aggregate_feedback():
    """
    Aggregate feedback data for model retraining analysis
    This endpoint can be called manually or by a scheduled task
    """
    from db_sync import run_feedback_aggregation_task
    
    # Run aggregation task
    result = run_feedback_aggregation_task()
    
    return jsonify(result), 200

# Get common pests for feedback dropdown
@app.route('/api/pests')
def get_pests():
    lang = request.args.get('lang', 'en')
    pests = PestDatabase.query.all()
    return jsonify([pest.to_dict(lang) for pest in pests])

# History API endpoints
@app.route('/api/history')
@login_required
def get_history():
    """
    Get scan history for current user
    Returns list of scans with date, pest_identified, confidence, severity
    Requirements: 6.1, 6.2
    """
    try:
        # Query PostgreSQL scans table filtered by current user
        # Join with pests table to get pest details
        # Order by created_at DESC
        scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).all()
        
        # Build response with required fields
        history_data = []
        for scan in scans:
            scan_dict = {
                'id': scan.id,
                'date': scan.created_at.isoformat() if scan.created_at else None,
                'pest_identified': scan.pest_identified,
                'pest_scientific': scan.pest_scientific,
                'confidence': round(scan.confidence * 100, 2) if scan.confidence else None,  # Convert to percentage
                'severity': scan.severity,
                'status': scan.status,
                'crop_type': scan.crop_type,
                'field_name': scan.field_name
            }
            history_data.append(scan_dict)
        
        logger.info(f"Retrieved {len(history_data)} scans for user {current_user.id}")
        return jsonify(history_data), 200
        
    except Exception as e:
        logger.error(f"Error retrieving scan history: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve scan history'}), 500


@app.route('/api/history/<int:scan_id>')
@login_required
def get_scan_detail(scan_id):
    """
    Get detailed information for a specific historical scan
    Includes PostgreSQL scan data, MongoDB metadata, and IPM recommendations
    Requirements: 6.3
    """
    from db_sync import get_detection_metadata
    from ipm_engine import get_recommendations, get_pest_by_name
    
    try:
        # Query PostgreSQL for scan record
        scan = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first()
        
        if not scan:
            return jsonify({'error': 'Scan not found or access denied'}), 404
        
        # Build base scan details
        scan_details = {
            'id': scan.id,
            'date': scan.created_at.isoformat() if scan.created_at else None,
            'pest_identified': scan.pest_identified,
            'pest_scientific': scan.pest_scientific,
            'confidence': round(scan.confidence * 100, 2) if scan.confidence else None,
            'severity': scan.severity,
            'status': scan.status,
            'crop_type': scan.crop_type,
            'field_name': scan.field_name,
            'damage_pattern': scan.damage_pattern,
            'model_version': scan.model_version,
            'image_path': scan.image_path
        }
        
        # Query MongoDB for detailed metadata using _id = "scan_{scan_id}"
        mongo_metadata = get_detection_metadata(scan_id)
        if mongo_metadata:
            scan_details['metadata'] = {
                'alternatives': mongo_metadata.get('alternatives', []),
                'image_info': mongo_metadata.get('image_info', {}),
                'model_details': mongo_metadata.get('model_details', {}),
                'location': mongo_metadata.get('location', {}),
                'flagged_for_retraining': mongo_metadata.get('flagged_for_retraining', False)
            }
        
        # Fetch associated recommendations from IPM engine
        pest = get_pest_by_name(scan.pest_identified, current_user.language)
        if pest:
            lang = current_user.language if current_user.language else 'en'
            recommendations = get_recommendations(
                pest_id=pest.id,
                crop=scan.crop_type,
                region=current_user.location,
                language=lang
            )
            scan_details['recommendations'] = recommendations
        else:
            scan_details['recommendations'] = []
        
        logger.info(f"Retrieved detailed scan information for scan_id={scan_id}")
        return jsonify(scan_details), 200
        
    except Exception as e:
        logger.error(f"Error retrieving scan detail: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve scan details'}), 500


# Export API endpoints
@app.route('/api/export/scans')
@login_required
def export_scans():
    """
    Export scan history in JSON or CSV format
    Requirements: 6.4
    """
    import csv
    import io
    from flask import make_response
    
    try:
        # Query all scans for current user
        scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).all()
        
        export_format = request.args.get('format', 'json')
        
        if export_format == 'json':
            # For JSON: return array of scan objects
            scans_data = []
            for scan in scans:
                scan_dict = {
                    'id': scan.id,
                    'date': scan.created_at.isoformat() if scan.created_at else None,
                    'pest_identified': scan.pest_identified,
                    'pest_scientific': scan.pest_scientific,
                    'confidence': round(scan.confidence * 100, 2) if scan.confidence else None,
                    'severity': scan.severity,
                    'status': scan.status,
                    'crop_type': scan.crop_type,
                    'field_name': scan.field_name,
                    'model_version': scan.model_version
                }
                scans_data.append(scan_dict)
            
            response = make_response(jsonify(scans_data))
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename=scan_history_{datetime.now().strftime("%Y%m%d")}.json'
            
            logger.info(f"Exported {len(scans_data)} scans as JSON for user {current_user.id}")
            return response
            
        elif export_format == 'csv':
            # For CSV: convert to CSV format with headers
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            headers = ['ID', 'Date', 'Pest Identified', 'Scientific Name', 'Confidence (%)', 
                      'Severity', 'Status', 'Crop Type', 'Field Name', 'Model Version']
            writer.writerow(headers)
            
            # Write data rows
            for scan in scans:
                row = [
                    scan.id,
                    scan.created_at.strftime('%Y-%m-%d %H:%M:%S') if scan.created_at else '',
                    scan.pest_identified or '',
                    scan.pest_scientific or '',
                    round(scan.confidence * 100, 2) if scan.confidence else '',
                    scan.severity or '',
                    scan.status or '',
                    scan.crop_type or '',
                    scan.field_name or '',
                    scan.model_version or ''
                ]
                writer.writerow(row)
            
            # Create response with CSV data
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=scan_history_{datetime.now().strftime("%Y%m%d")}.csv'
            
            logger.info(f"Exported {len(scans)} scans as CSV for user {current_user.id}")
            return response
            
        else:
            return jsonify({'error': 'Unsupported format. Use format=json or format=csv'}), 400
            
    except Exception as e:
        logger.error(f"Error exporting scans: {e}", exc_info=True)
        return jsonify({'error': 'Failed to export scan history'}), 500

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
    """Handle image upload and analysis"""
    from ai_client import call_ai_service
    from confidence_utils import classify_confidence, should_request_feedback
    from ipm_engine import get_recommendations, get_pest_by_name
    from db_sync import sync_detection_metadata
    
    try:
        # Check if file was uploaded
        filepath = None
        if 'image' not in request.files:
            # Check if base64 image was sent
            json_data = request.get_json(silent=True)
            if json_data and 'image_data' in json_data:
                image_data = json_data['image_data']
                # Process base64 image
                image_str = image_data.split(',')[1] if ',' in image_data else image_data
                image_bytes = base64.b64decode(image_str)
                
                # Save base64 image to file
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_capture.jpg"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
            else:
                return jsonify({'error': 'No image provided'}), 400
        else:
            file = request.files['image']
            if file and allowed_file(file.filename):
                # Save uploaded file
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
            else:
                return jsonify({'error': 'Invalid file format'}), 400

        # Call AI microservice
        ai_result = call_ai_service(filepath)
        
        # Check if AI service call was successful
        if not ai_result.get('success'):
            return jsonify({'error': ai_result.get('error', 'AI service error')}), 500
        
        # Extract AI response data
        pest_label = ai_result.get('pest_label')
        scientific_name = ai_result.get('scientific_name')
        confidence = ai_result.get('confidence')
        alternatives = ai_result.get('alternatives', [])
        processing_time_ms = ai_result.get('processing_time_ms')
        timing_breakdown = ai_result.get('timing_breakdown', {})
        fallback_used = ai_result.get('fallback_used', False)
        
        # Classify confidence level
        confidence_level = classify_confidence(confidence)
        
        # Look up pest details from database
        pest = get_pest_by_name(pest_label, current_user.language)
        pest_id = pest.id if pest else None
        
        # Get localized pest name if available
        if pest:
            lang = current_user.language if current_user.language else 'en'
            name_field = f'name_{lang}'
            localized_name = getattr(pest, name_field, None) if lang != 'en' else None
            pest_common_name = localized_name or pest.common_name
            pest_scientific_name = pest.scientific_name or scientific_name
        else:
            pest_common_name = pest_label
            pest_scientific_name = scientific_name
        
        # Get IPM recommendations
        recommendations = []
        if pest_id:
            crop_type = request.form.get('crop_type') or current_user.crops
            region = current_user.location
            lang = current_user.language if current_user.language else 'en'
            
            recommendations = get_recommendations(
                pest_id=pest_id,
                crop=crop_type,
                region=region,
                language=lang
            )
        
        # Store scan in PostgreSQL
        scan = Scan(
            user_id=current_user.id,
            image_path=filepath,
            pest_identified=pest_common_name,
            pest_scientific=pest_scientific_name,
            confidence=confidence,
            status='identified',
            model_version=timing_breakdown.get('primary_model', 'v1.0.0')
        )
        
        db.session.add(scan)
        db.session.commit()
        
        # Get the scan ID after commit
        scan_id = scan.id
        
        # Prepare image info for MongoDB
        image_info = {
            'filename': os.path.basename(filepath),
            'file_size_kb': os.path.getsize(filepath) / 1024 if os.path.exists(filepath) else 0
        }
        
        # Prepare model details for MongoDB
        model_details = {
            'primary_model': 'EfficientNet-B0',
            'primary_version': 'v2.1.0',
            'fallback_used': fallback_used,
            'preprocessing_time_ms': timing_breakdown.get('preprocessing_ms', 0),
            'inference_time_ms': timing_breakdown.get('primary_inference_ms', 0) + timing_breakdown.get('fallback_inference_ms', 0),
            'total_time_ms': processing_time_ms
        }
        
        # Sync to MongoDB asynchronously
        sync_detection_metadata(
            scan_id=scan_id,
            user_id=current_user.id,
            pest_label=pest_label,
            confidence=confidence,
            alternatives=alternatives,
            image_info=image_info,
            model_details=model_details,
            location=None  # TODO: Add location data if available
        )
        
        # Build complete response
        analysis_result = {
            'success': True,
            'scan_id': scan_id,
            'pest_identified': pest_common_name,
            'pest_scientific': pest_scientific_name,
            'confidence': round(confidence * 100, 2),  # Convert to percentage
            'confidence_level': confidence_level,
            'alternatives': alternatives,
            'recommendations': recommendations,
            'processing_time_ms': processing_time_ms,
            'should_request_feedback': should_request_feedback(confidence),
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(analysis_result)

    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def results():
    """Display analysis results"""
    # Get the latest scan result or use sample data
    if scan_history:
        latest_result = scan_history[-1]['result']
    else:
        latest_result = {
            'status': 'Pest Damaged',
            'pest_identified': 'Japanese Beetle',
            'pest_scientific': 'Popillia japonica',
            'confidence': 94,
            'damage_pattern': 'Skeletonized leaves with lace-like appearance',
            'immediate_action': True,
            'treatments': {
                'immediate': [
                    'Hand-pick beetles in early morning when they are less active',
                    'Shake beetles into soapy water for disposal',
                    'Remove heavily damaged leaves to prevent further stress'
                ],
                'ipm': [
                    'Apply neem oil spray (follow label instructions)',
                    'Use row covers to protect vulnerable plants',
                    'Consider beneficial nematodes for soil treatment'
                ],
                'prevention': [
                    'Monitor plants daily during peak season (June-August)',
                    'Avoid planting highly susceptible plants near each other',
                    'Maintain healthy soil to improve plant resilience'
                ]
            }
        }
    
    return render_template('results.html', result=latest_result, 
                         timestamp=datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p'))



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

    app.run(debug=True, host='0.0.0.0', port=5001)
