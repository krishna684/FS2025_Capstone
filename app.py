from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from datetime import datetime, timedelta
import random
import base64
import io
from PIL import Image
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

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

@app.route('/')
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
def analyze():
    """Handle image upload and analysis"""
    try:
        # Check if file was uploaded
        if 'image' not in request.files:
            # Check if base64 image was sent
            json_data = request.get_json(silent=True)
            if json_data and 'image_data' in json_data:
                image_data = json_data['image_data']
                # Process base64 image
                image_str = image_data.split(',')[1] if ',' in image_data else image_data
                image_bytes = base64.b64decode(image_str)
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

        # Simulate AI analysis (in production, call your ML model here)
        analysis_result = simulate_pest_detection()

        # Store in history
        scan_history.append({
            'timestamp': datetime.now().isoformat(),
            'result': analysis_result
        })

        return jsonify(analysis_result)

    except Exception as e:
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

def simulate_pest_detection():
    """Simulate pest detection (replace with actual ML model)"""
    pests = [
        {
            'name': 'Japanese Beetle',
            'scientific': 'Popillia japonica',
            'damage': 'Skeletonized leaves with lace-like appearance',
            'severity': 'Moderate'
        },
        {
            'name': 'Aphids',
            'scientific': 'Aphidoidea',
            'damage': 'Curled leaves, sticky honeydew on plant surface',
            'severity': 'Mild'
        },
        {
            'name': 'Spider Mites',
            'scientific': 'Tetranychidae',
            'damage': 'Fine webbing and yellow stippling on leaves',
            'severity': 'Severe'
        },
        {
            'name': 'No Pest Detected',
            'scientific': 'N/A',
            'damage': 'Plant appears healthy',
            'severity': 'Healthy'
        }
    ]
    
    # Randomly select a pest (weighted towards pest detection for demo)
    weights = [0.3, 0.25, 0.2, 0.25]  # Weights for each pest
    selected = random.choices(pests, weights=weights)[0]
    
    if selected['name'] == 'No Pest Detected':
        return {
            'status': 'Healthy',
            'pest_identified': 'None',
            'confidence': random.randint(92, 99),
            'message': 'Your plant appears to be healthy!'
        }
    
    return {
        'status': 'Pest Damaged',
        'pest_identified': selected['name'],
        'pest_scientific': selected['scientific'],
        'confidence': random.randint(85, 98),
        'damage_pattern': selected['damage'],
        'severity': selected['severity'],
        'immediate_action': selected['severity'] in ['Moderate', 'Severe'],
        'treatments': {
            'immediate': [
                'Hand-pick pests if visible',
                'Isolate affected plants',
                'Remove damaged leaves'
            ],
            'ipm': [
                'Apply appropriate organic pesticide',
                'Introduce beneficial insects',
                'Use physical barriers'
            ],
            'prevention': [
                'Regular monitoring',
                'Maintain plant health',
                'Crop rotation'
            ]
        }
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
    app.run(debug=True, host='0.0.0.0', port=5001)
