from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from database import db

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(10), default='en')  # en, hi, es, sw, etc.
    units = db.Column(db.String(10), default='metric')  # metric or imperial
    theme = db.Column(db.String(20), default='emerald')  # emerald, forest, ocean, sunset
    farm_name = db.Column(db.String(100), nullable=True)
    farm_size = db.Column(db.String(50), nullable=True)
    crops = db.Column(db.Text, nullable=True)  # Comma-separated crop list
    notification_email = db.Column(db.Boolean, default=True)
    notification_push = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    # OAuth fields
    oauth_provider = db.Column(db.String(50), nullable=True)  # google, microsoft
    oauth_id = db.Column(db.String(255), nullable=True)

    # Relationships
    scans = db.relationship('Scan', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    feedbacks = db.relationship('Feedback', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'location': self.location,
            'language': self.language,
            'units': self.units,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Scan(db.Model):
    """Scan history model"""
    __tablename__ = 'scans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    image_path = db.Column(db.String(255), nullable=True)
    pest_identified = db.Column(db.String(100), nullable=True, index=True)
    pest_scientific = db.Column(db.String(100), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=True)  # identified, corrected, verified
    severity = db.Column(db.String(50), nullable=True)  # mild, moderate, severe, healthy
    crop_type = db.Column(db.String(100), nullable=True)
    field_name = db.Column(db.String(100), nullable=True)
    damage_pattern = db.Column(db.Text, nullable=True)
    model_version = db.Column(db.String(20), nullable=True)  # For model traceability
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    feedbacks = db.relationship('Feedback', backref='scan', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """Convert scan to dictionary"""
        return {
            'id': self.id,
            'pest_identified': self.pest_identified,
            'pest_scientific': self.pest_scientific,
            'confidence': self.confidence,
            'status': self.status,
            'severity': self.severity,
            'crop_type': self.crop_type,
            'field_name': self.field_name,
            'model_version': self.model_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'has_feedback': self.feedbacks.count() > 0
        }


class Feedback(db.Model):
    """User feedback on scan results"""
    __tablename__ = 'feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False, index=True)

    # Feedback type
    is_correct = db.Column(db.Boolean, nullable=False)  # True if AI was correct

    # If incorrect, what was the actual pest?
    actual_pest_name = db.Column(db.String(100), nullable=True)
    actual_pest_scientific = db.Column(db.String(100), nullable=True)

    # Additional notes from user
    notes = db.Column(db.Text, nullable=True)

    # Was this feedback helpful for the user?
    helpful = db.Column(db.Boolean, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert feedback to dictionary"""
        return {
            'id': self.id,
            'is_correct': self.is_correct,
            'actual_pest_name': self.actual_pest_name,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PestDatabase(db.Model):
    """Common pests database for feedback dropdown"""
    __tablename__ = 'pests'

    id = db.Column(db.Integer, primary_key=True)
    common_name = db.Column(db.String(100), nullable=False, index=True)
    scientific_name = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(50), nullable=True, index=True)  # insect, disease, fungal
    description = db.Column(db.Text, nullable=True)

    # Multilingual support
    name_es = db.Column(db.String(100), nullable=True)  # Spanish
    name_hi = db.Column(db.String(100), nullable=True)  # Hindi
    name_sw = db.Column(db.String(100), nullable=True)  # Swahili

    def to_dict(self, language='en'):
        """Convert pest to dictionary with language support"""
        name_field = f'name_{language}'
        localized_name = getattr(self, name_field, None) if language != 'en' else None

        return {
            'id': self.id,
            'common_name': localized_name or self.common_name,
            'scientific_name': self.scientific_name,
            'category': self.category
        }


class Treatment(db.Model):
    """Treatment options for pest management"""
    __tablename__ = 'treatments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # cultural, biological, chemical
    description = db.Column(db.Text, nullable=True)
    
    # Multilingual descriptions
    description_es = db.Column(db.Text, nullable=True)
    description_hi = db.Column(db.Text, nullable=True)
    description_sw = db.Column(db.Text, nullable=True)
    
    cost_estimate = db.Column(db.String(50), nullable=True)
    effectiveness_rate = db.Column(db.Float, nullable=True)

    def to_dict(self, language='en'):
        """Convert treatment to dictionary with language support"""
        desc_field = f'description_{language}'
        localized_desc = getattr(self, desc_field, None) if language != 'en' else None

        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'description': localized_desc or self.description,
            'cost_estimate': self.cost_estimate,
            'effectiveness_rate': self.effectiveness_rate
        }


class IPMRecommendation(db.Model):
    """IPM recommendations linking pests to treatments"""
    __tablename__ = 'ipm_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    pest_id = db.Column(db.Integer, db.ForeignKey('pests.id'), nullable=False, index=True)
    treatment_id = db.Column(db.Integer, db.ForeignKey('treatments.id'), nullable=False)
    priority = db.Column(db.String(20), nullable=True)  # primary, secondary, last_resort
    region = db.Column(db.String(50), nullable=True, index=True)  # region code or 'global'
    crop_type = db.Column(db.String(50), nullable=True)
    conditions = db.Column(db.Text, nullable=True)  # JSON string with additional conditions
    success_rate = db.Column(db.Float, nullable=True)

    # Relationships
    pest = db.relationship('PestDatabase', backref='recommendations')
    treatment = db.relationship('Treatment', backref='recommendations')

    def to_dict(self, language='en'):
        """Convert IPM recommendation to dictionary"""
        return {
            'id': self.id,
            'pest': self.pest.to_dict(language) if self.pest else None,
            'treatment': self.treatment.to_dict(language) if self.treatment else None,
            'priority': self.priority,
            'region': self.region,
            'crop_type': self.crop_type,
            'success_rate': self.success_rate
        }
