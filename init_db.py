"""
Database initialization script for PostgreSQL schema
Creates all tables and indexes
"""
import os
import sys
import logging

# Set Flask environment before importing app
os.environ['FLASK_ENV'] = 'development'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_database():
    """Initialize PostgreSQL and MongoDB databases"""
    # Import here to avoid circular imports
    from app import app
    from database import db
    from models import User, Scan, Feedback, PestDatabase, Treatment, IPMRecommendation
    
    with app.app_context():
        logger.info("Initializing databases...")
        
        # Create all PostgreSQL tables
        logger.info("Creating PostgreSQL tables...")
        db.create_all()
        logger.info("PostgreSQL tables created successfully")
        
        # Seed initial data if needed
        seed_initial_data()
        
        logger.info("Database initialization complete!")


def seed_initial_data():
    """Seed initial pest and treatment data"""
    from database import db
    from models import PestDatabase, Treatment, IPMRecommendation
    
    # Check if pests already exist
    if PestDatabase.query.count() > 0:
        logger.info("Pests already seeded, skipping...")
        return
    
    logger.info("Seeding initial pest data...")
    
    # Add common pests
    pests = [
        PestDatabase(
            common_name='Fall Armyworm',
            scientific_name='Spodoptera frugiperda',
            category='insect',
            description='A destructive pest that feeds on corn, rice, and other crops',
            name_es='Gusano Cogollero',
            name_hi='फॉल आर्मीवर्म',
            name_sw='Mdudu wa Jeshi'
        ),
        PestDatabase(
            common_name='Aphids',
            scientific_name='Aphidoidea',
            category='insect',
            description='Small sap-sucking insects that damage plants',
            name_es='Pulgones',
            name_hi='एफिड्स',
            name_sw='Dudu wa Majani'
        ),
        PestDatabase(
            common_name='Tomato Leafminer',
            scientific_name='Tuta absoluta',
            category='insect',
            description='Devastating pest of tomato crops',
            name_es='Polilla del Tomate',
            name_hi='टमाटर लीफमाइनर',
            name_sw='Mdudu wa Nyanya'
        ),
        PestDatabase(
            common_name='Whitefly',
            scientific_name='Aleyrodidae',
            category='insect',
            description='Tiny white insects that transmit plant viruses',
            name_es='Mosca Blanca',
            name_hi='सफेद मक्खी',
            name_sw='Nzi Mweupe'
        ),
        PestDatabase(
            common_name='Spider Mites',
            scientific_name='Tetranychidae',
            category='insect',
            description='Tiny arachnids that cause leaf damage',
            name_es='Ácaros',
            name_hi='मकड़ी के कण',
            name_sw='Panya wa Utando'
        ),
        PestDatabase(
            common_name='Japanese Beetle',
            scientific_name='Popillia japonica',
            category='insect',
            description='Metallic green beetle that skeletonizes leaves',
            name_es='Escarabajo Japonés',
            name_hi='जापानी बीटल',
            name_sw='Mdudu wa Kijapani'
        ),
        PestDatabase(
            common_name='Cabbage Worm',
            scientific_name='Pieris rapae',
            category='insect',
            description='Green caterpillar that feeds on brassicas',
            name_es='Gusano de la Col',
            name_hi='पत्ता गोभी का कीड़ा',
            name_sw='Funza la Kabichi'
        ),
    ]
    
    db.session.add_all(pests)
    db.session.commit()
    logger.info(f"Added {len(pests)} pests to database")
    
    # Add treatments
    logger.info("Seeding treatment data...")
    
    treatments = [
        # Cultural controls
        Treatment(
            name='Crop Rotation',
            type='cultural',
            description='Rotate crops to break pest life cycles',
            description_es='Rotar cultivos para romper ciclos de vida de plagas',
            description_hi='कीट जीवन चक्र को तोड़ने के लिए फसल चक्र',
            description_sw='Zunguka mazao ili kuvunja mizunguko ya wadudu',
            cost_estimate='Low',
            effectiveness_rate=0.7
        ),
        Treatment(
            name='Hand-picking',
            type='cultural',
            description='Manually remove pests from plants',
            description_es='Eliminar plagas manualmente de las plantas',
            description_hi='पौधों से कीटों को मैन्युअल रूप से हटाएं',
            description_sw='Ondoa wadudu kwa mkono kutoka kwa mimea',
            cost_estimate='Low',
            effectiveness_rate=0.6
        ),
        Treatment(
            name='Intercropping',
            type='cultural',
            description='Plant multiple crops together to confuse pests',
            description_es='Plantar múltiples cultivos juntos para confundir plagas',
            description_hi='कीटों को भ्रमित करने के लिए कई फसलें एक साथ लगाएं',
            description_sw='Panda mazao mengi pamoja ili kuchanganya wadudu',
            cost_estimate='Low',
            effectiveness_rate=0.65
        ),
        # Biological controls
        Treatment(
            name='Parasitic Wasps',
            type='biological',
            description='Release beneficial wasps that parasitize pest eggs',
            description_es='Liberar avispas beneficiosas que parasitan huevos de plagas',
            description_hi='लाभकारी ततैया छोड़ें जो कीट अंडे को परजीवी बनाते हैं',
            description_sw='Achilia nyigu wenye manufaa wanaoshambulia mayai ya wadudu',
            cost_estimate='Medium',
            effectiveness_rate=0.8
        ),
        Treatment(
            name='Ladybugs',
            type='biological',
            description='Introduce ladybugs to control aphids',
            description_es='Introducir mariquitas para controlar pulgones',
            description_hi='एफिड्स को नियंत्रित करने के लिए लेडीबग्स पेश करें',
            description_sw='Weka dudu wa ladybug kudhibiti wadudu wa majani',
            cost_estimate='Medium',
            effectiveness_rate=0.75
        ),
        Treatment(
            name='Neem Oil',
            type='biological',
            description='Apply organic neem oil spray',
            description_es='Aplicar spray orgánico de aceite de neem',
            description_hi='जैविक नीम तेल स्प्रे लगाएं',
            description_sw='Tumia dawa ya mafuta ya mwarobaini',
            cost_estimate='Low',
            effectiveness_rate=0.7
        ),
        Treatment(
            name='Bacillus thuringiensis (BT)',
            type='biological',
            description='Apply BT bacterial spray for caterpillar control',
            description_es='Aplicar spray bacteriano BT para control de orugas',
            description_hi='कैटरपिलर नियंत्रण के लिए बीटी बैक्टीरियल स्प्रे लगाएं',
            description_sw='Tumia dawa ya bakteria ya BT kudhibiti mabuu',
            cost_estimate='Medium',
            effectiveness_rate=0.85
        ),
        # Chemical controls (last resort)
        Treatment(
            name='Pyrethroid Insecticide',
            type='chemical',
            description='Synthetic insecticide - USE AS LAST RESORT. Follow all safety precautions.',
            description_es='Insecticida sintético - USAR COMO ÚLTIMO RECURSO. Siga todas las precauciones de seguridad.',
            description_hi='सिंथेटिक कीटनाशक - अंतिम उपाय के रूप में उपयोग करें। सभी सुरक्षा सावधानियों का पालन करें।',
            description_sw='Dawa ya wadudu ya sintetiki - TUMIA KWA HALI YA DHARURA. Fuata tahadhari zote za usalama.',
            cost_estimate='High',
            effectiveness_rate=0.9
        ),
        Treatment(
            name='Organophosphate',
            type='chemical',
            description='Chemical pesticide - USE AS LAST RESORT. Highly toxic, use protective equipment.',
            description_es='Pesticida químico - USAR COMO ÚLTIMO RECURSO. Altamente tóxico, use equipo de protección.',
            description_hi='रासायनिक कीटनाशक - अंतिम उपाय के रूप में उपयोग करें। अत्यधिक विषैला, सुरक्षात्मक उपकरण का उपयोग करें।',
            description_sw='Dawa ya kemikali - TUMIA KWA HALI YA DHARURA. Sumu sana, tumia vifaa vya ulinzi.',
            cost_estimate='High',
            effectiveness_rate=0.95
        ),
    ]
    
    db.session.add_all(treatments)
    db.session.commit()
    logger.info(f"Added {len(treatments)} treatments to database")
    
    # Create IPM recommendations
    logger.info("Creating IPM recommendations...")
    
    # Get pest and treatment IDs
    fall_armyworm = PestDatabase.query.filter_by(common_name='Fall Armyworm').first()
    aphids = PestDatabase.query.filter_by(common_name='Aphids').first()
    tomato_leafminer = PestDatabase.query.filter_by(common_name='Tomato Leafminer').first()
    whitefly = PestDatabase.query.filter_by(common_name='Whitefly').first()
    spider_mites = PestDatabase.query.filter_by(common_name='Spider Mites').first()
    
    crop_rotation = Treatment.query.filter_by(name='Crop Rotation').first()
    hand_picking = Treatment.query.filter_by(name='Hand-picking').first()
    intercropping = Treatment.query.filter_by(name='Intercropping').first()
    parasitic_wasps = Treatment.query.filter_by(name='Parasitic Wasps').first()
    ladybugs = Treatment.query.filter_by(name='Ladybugs').first()
    neem_oil = Treatment.query.filter_by(name='Neem Oil').first()
    bt_spray = Treatment.query.filter_by(name='Bacillus thuringiensis (BT)').first()
    pyrethroid = Treatment.query.filter_by(name='Pyrethroid Insecticide').first()
    organophosphate = Treatment.query.filter_by(name='Organophosphate').first()
    
    recommendations = []
    
    # Fall Armyworm recommendations
    if fall_armyworm:
        recommendations.extend([
            IPMRecommendation(pest_id=fall_armyworm.id, treatment_id=hand_picking.id, 
                            priority='primary', region='global', success_rate=0.6),
            IPMRecommendation(pest_id=fall_armyworm.id, treatment_id=bt_spray.id, 
                            priority='primary', region='global', success_rate=0.85),
            IPMRecommendation(pest_id=fall_armyworm.id, treatment_id=parasitic_wasps.id, 
                            priority='secondary', region='global', success_rate=0.8),
            IPMRecommendation(pest_id=fall_armyworm.id, treatment_id=pyrethroid.id, 
                            priority='last_resort', region='global', success_rate=0.9),
        ])
    
    # Aphids recommendations
    if aphids:
        recommendations.extend([
            IPMRecommendation(pest_id=aphids.id, treatment_id=ladybugs.id, 
                            priority='primary', region='global', success_rate=0.75),
            IPMRecommendation(pest_id=aphids.id, treatment_id=neem_oil.id, 
                            priority='primary', region='global', success_rate=0.7),
            IPMRecommendation(pest_id=aphids.id, treatment_id=hand_picking.id, 
                            priority='secondary', region='global', success_rate=0.5),
            IPMRecommendation(pest_id=aphids.id, treatment_id=pyrethroid.id, 
                            priority='last_resort', region='global', success_rate=0.9),
        ])
    
    # Tomato Leafminer recommendations
    if tomato_leafminer:
        recommendations.extend([
            IPMRecommendation(pest_id=tomato_leafminer.id, treatment_id=parasitic_wasps.id, 
                            priority='primary', region='global', success_rate=0.8),
            IPMRecommendation(pest_id=tomato_leafminer.id, treatment_id=bt_spray.id, 
                            priority='primary', region='global', success_rate=0.75),
            IPMRecommendation(pest_id=tomato_leafminer.id, treatment_id=crop_rotation.id, 
                            priority='secondary', region='global', success_rate=0.7),
            IPMRecommendation(pest_id=tomato_leafminer.id, treatment_id=organophosphate.id, 
                            priority='last_resort', region='global', success_rate=0.95),
        ])
    
    # Whitefly recommendations
    if whitefly:
        recommendations.extend([
            IPMRecommendation(pest_id=whitefly.id, treatment_id=neem_oil.id, 
                            priority='primary', region='global', success_rate=0.7),
            IPMRecommendation(pest_id=whitefly.id, treatment_id=intercropping.id, 
                            priority='secondary', region='global', success_rate=0.65),
            IPMRecommendation(pest_id=whitefly.id, treatment_id=pyrethroid.id, 
                            priority='last_resort', region='global', success_rate=0.85),
        ])
    
    # Spider Mites recommendations
    if spider_mites:
        recommendations.extend([
            IPMRecommendation(pest_id=spider_mites.id, treatment_id=neem_oil.id, 
                            priority='primary', region='global', success_rate=0.7),
            IPMRecommendation(pest_id=spider_mites.id, treatment_id=ladybugs.id, 
                            priority='secondary', region='global', success_rate=0.6),
            IPMRecommendation(pest_id=spider_mites.id, treatment_id=pyrethroid.id, 
                            priority='last_resort', region='global', success_rate=0.9),
        ])
    
    db.session.add_all(recommendations)
    db.session.commit()
    logger.info(f"Added {len(recommendations)} IPM recommendations to database")


if __name__ == '__main__':
    initialize_database()
