"""
Seed IPM recommendation database with common pests and treatments

This script populates the database with:
- Common agricultural pests
- Cultural, biological, and chemical treatments
- IPM recommendations linking pests to treatments with priorities
"""

from app import app
from database import db
from models import PestDatabase, Treatment, IPMRecommendation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_pests():
    """Add common pests to the database"""
    pests_data = [
        {
            'common_name': 'Fall Armyworm',
            'scientific_name': 'Spodoptera frugiperda',
            'category': 'insect',
            'description': 'Destructive caterpillar pest that feeds on corn, sorghum, and other crops',
            'name_es': 'Gusano Cogollero',
            'name_hi': 'फॉल आर्मीवर्म',
            'name_sw': 'Mdudu wa Jeshi'
        },
        {
            'common_name': 'Aphids',
            'scientific_name': 'Aphidoidea',
            'category': 'insect',
            'description': 'Small sap-sucking insects that weaken plants and transmit viruses',
            'name_es': 'Pulgones',
            'name_hi': 'एफिड्स',
            'name_sw': 'Dudu wa Majani'
        },
        {
            'common_name': 'Tomato Leafminer',
            'scientific_name': 'Tuta absoluta',
            'category': 'insect',
            'description': 'Devastating pest of tomatoes that mines leaves, stems, and fruits',
            'name_es': 'Polilla del Tomate',
            'name_hi': 'टमाटर लीफमाइनर',
            'name_sw': 'Mdudu wa Nyanya'
        },
        {
            'common_name': 'Whitefly',
            'scientific_name': 'Aleyrodidae',
            'category': 'insect',
            'description': 'Tiny white flying insects that suck plant sap and spread diseases',
            'name_es': 'Mosca Blanca',
            'name_hi': 'सफेद मक्खी',
            'name_sw': 'Nzi Weupe'
        },
        {
            'common_name': 'Spider Mites',
            'scientific_name': 'Tetranychidae',
            'category': 'insect',
            'description': 'Microscopic pests that cause stippling and webbing on leaves',
            'name_es': 'Ácaros',
            'name_hi': 'मकड़ी के कण',
            'name_sw': 'Panya wa Utando'
        }
    ]
    
    created_pests = []
    for pest_data in pests_data:
        # Check if pest already exists
        existing = PestDatabase.query.filter_by(common_name=pest_data['common_name']).first()
        if existing:
            logger.info(f"Pest already exists: {pest_data['common_name']}")
            created_pests.append(existing)
            continue
        
        pest = PestDatabase(**pest_data)
        db.session.add(pest)
        created_pests.append(pest)
        logger.info(f"Added pest: {pest_data['common_name']}")
    
    db.session.commit()
    return created_pests


def seed_treatments():
    """Add cultural, biological, and chemical treatments"""
    treatments_data = [
        # Cultural controls
        {
            'name': 'Crop Rotation',
            'type': 'cultural',
            'description': 'Rotate crops annually to break pest life cycles and reduce pest populations',
            'description_es': 'Rotar cultivos anualmente para romper ciclos de vida de plagas',
            'description_hi': 'कीट जीवन चक्र को तोड़ने के लिए फसल चक्र',
            'description_sw': 'Zunguka mazao kila mwaka kupunguza wadudu',
            'cost_estimate': 'Low',
            'effectiveness_rate': 0.75
        },
        {
            'name': 'Intercropping',
            'type': 'cultural',
            'description': 'Plant multiple crops together to confuse pests and reduce damage',
            'description_es': 'Plantar múltiples cultivos juntos para confundir plagas',
            'description_hi': 'कीटों को भ्रमित करने के लिए मिश्रित खेती',
            'description_sw': 'Panda mazao mchanganyiko kupunguza wadudu',
            'cost_estimate': 'Low',
            'effectiveness_rate': 0.70
        },
        {
            'name': 'Hand-picking',
            'type': 'cultural',
            'description': 'Manually remove visible pests from plants, especially effective for large caterpillars',
            'description_es': 'Eliminar manualmente las plagas visibles de las plantas',
            'description_hi': 'पौधों से कीटों को हाथ से हटाना',
            'description_sw': 'Ondoa wadudu kwa mkono kutoka kwa mimea',
            'cost_estimate': 'Very Low',
            'effectiveness_rate': 0.65
        },
        {
            'name': 'Trap Crops',
            'type': 'cultural',
            'description': 'Plant attractive crops to lure pests away from main crops',
            'description_es': 'Plantar cultivos atractivos para alejar plagas',
            'description_hi': 'मुख्य फसलों से कीटों को दूर करने के लिए जाल फसलें',
            'description_sw': 'Panda mazao ya kuvutia wadudu mbali na mazao makuu',
            'cost_estimate': 'Low',
            'effectiveness_rate': 0.68
        },
        {
            'name': 'Sanitation and Field Hygiene',
            'type': 'cultural',
            'description': 'Remove crop residues and weeds that harbor pests',
            'description_es': 'Eliminar residuos de cultivos y malezas que albergan plagas',
            'description_hi': 'कीटों को आश्रय देने वाले फसल अवशेषों को हटाना',
            'description_sw': 'Ondoa mabaki ya mazao na magugu yanayohifadhi wadudu',
            'cost_estimate': 'Very Low',
            'effectiveness_rate': 0.72
        },
        
        # Biological controls
        {
            'name': 'Parasitic Wasps (Trichogramma)',
            'type': 'biological',
            'description': 'Release parasitic wasps that lay eggs in pest eggs, preventing hatching',
            'description_es': 'Liberar avispas parasitarias que ponen huevos en huevos de plagas',
            'description_hi': 'परजीवी ततैया जो कीट अंडों में अंडे देते हैं',
            'description_sw': 'Achilia manyigu wa parasitic wanaoweka mayai kwenye mayai ya wadudu',
            'cost_estimate': 'Medium',
            'effectiveness_rate': 0.80
        },
        {
            'name': 'Ladybugs (Coccinellidae)',
            'type': 'biological',
            'description': 'Introduce ladybugs that feed on aphids and other soft-bodied pests',
            'description_es': 'Introducir mariquitas que se alimentan de pulgones',
            'description_hi': 'लेडीबग्स जो एफिड्स खाते हैं',
            'description_sw': 'Walete dudu mzuri wanaokula wadudu wadogo',
            'cost_estimate': 'Medium',
            'effectiveness_rate': 0.78
        },
        {
            'name': 'Neem Oil Spray',
            'type': 'biological',
            'description': 'Apply organic neem oil to disrupt pest feeding and reproduction',
            'description_es': 'Aplicar aceite de neem orgánico para interrumpir alimentación de plagas',
            'description_hi': 'कीट भोजन और प्रजनन को बाधित करने के लिए नीम तेल',
            'description_sw': 'Tumia mafuta ya mwarobaini kudhibiti wadudu',
            'cost_estimate': 'Low',
            'effectiveness_rate': 0.73
        },
        {
            'name': 'Bacillus thuringiensis (Bt) Spray',
            'type': 'biological',
            'description': 'Apply Bt bacteria that specifically target caterpillars without harming beneficial insects',
            'description_es': 'Aplicar bacteria Bt que ataca específicamente orugas',
            'description_hi': 'बीटी बैक्टीरिया जो विशेष रूप से कैटरपिलर को लक्षित करता है',
            'description_sw': 'Tumia bakteria ya Bt inayoshambulia mabuu',
            'cost_estimate': 'Medium',
            'effectiveness_rate': 0.82
        },
        {
            'name': 'Entomopathogenic Nematodes',
            'type': 'biological',
            'description': 'Apply beneficial nematodes to soil to control soil-dwelling pests',
            'description_es': 'Aplicar nematodos beneficiosos al suelo para controlar plagas',
            'description_hi': 'मिट्टी में रहने वाले कीटों को नियंत्रित करने के लिए नेमाटोड',
            'description_sw': 'Tumia nematodi zenye manufaa kudhibiti wadudu wa udongoni',
            'cost_estimate': 'Medium',
            'effectiveness_rate': 0.76
        },
        
        # Chemical controls (last resort)
        {
            'name': 'Synthetic Pyrethroid Insecticide',
            'type': 'chemical',
            'description': 'Broad-spectrum synthetic insecticide for severe infestations. Use only when other methods fail.',
            'description_es': 'Insecticida sintético de amplio espectro para infestaciones graves',
            'description_hi': 'गंभीर संक्रमण के लिए सिंथेटिक कीटनाशक',
            'description_sw': 'Dawa ya wadudu ya kemikali kwa maambukizi makubwa',
            'cost_estimate': 'High',
            'effectiveness_rate': 0.90
        },
        {
            'name': 'Organophosphate Insecticide',
            'type': 'chemical',
            'description': 'Powerful chemical insecticide for resistant pests. Requires protective equipment and careful application.',
            'description_es': 'Insecticida químico potente para plagas resistentes',
            'description_hi': 'प्रतिरोधी कीटों के लिए शक्तिशाली रासायनिक कीटनाशक',
            'description_sw': 'Dawa kali ya kemikali kwa wadudu wenye nguvu',
            'cost_estimate': 'High',
            'effectiveness_rate': 0.92
        },
        {
            'name': 'Systemic Insecticide',
            'type': 'chemical',
            'description': 'Chemical absorbed by plant to kill feeding pests. Use as last resort with caution.',
            'description_es': 'Químico absorbido por la planta para matar plagas',
            'description_hi': 'पौधे द्वारा अवशोषित रसायन जो कीटों को मारता है',
            'description_sw': 'Kemikali inayofyonzwa na mmea kuua wadudu',
            'cost_estimate': 'High',
            'effectiveness_rate': 0.88
        }
    ]
    
    created_treatments = []
    for treatment_data in treatments_data:
        # Check if treatment already exists
        existing = Treatment.query.filter_by(name=treatment_data['name']).first()
        if existing:
            logger.info(f"Treatment already exists: {treatment_data['name']}")
            created_treatments.append(existing)
            continue
        
        treatment = Treatment(**treatment_data)
        db.session.add(treatment)
        created_treatments.append(treatment)
        logger.info(f"Added treatment: {treatment_data['name']}")
    
    db.session.commit()
    return created_treatments


def seed_ipm_recommendations(pests, treatments):
    """Link pests to treatments with IPM priorities"""
    
    # Helper function to find pest by name
    def find_pest(name):
        return next((p for p in pests if p.common_name == name), None)
    
    # Helper function to find treatment by name
    def find_treatment(name):
        return next((t for t in treatments if t.name == name), None)
    
    recommendations_data = [
        # Fall Armyworm recommendations
        {'pest': 'Fall Armyworm', 'treatment': 'Hand-picking', 'priority': 'primary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.65},
        {'pest': 'Fall Armyworm', 'treatment': 'Crop Rotation', 'priority': 'primary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.75},
        {'pest': 'Fall Armyworm', 'treatment': 'Trap Crops', 'priority': 'primary', 'region': 'global', 'crop_type': 'corn', 'success_rate': 0.68},
        {'pest': 'Fall Armyworm', 'treatment': 'Parasitic Wasps (Trichogramma)', 'priority': 'primary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.80},
        {'pest': 'Fall Armyworm', 'treatment': 'Bacillus thuringiensis (Bt) Spray', 'priority': 'secondary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.82},
        {'pest': 'Fall Armyworm', 'treatment': 'Synthetic Pyrethroid Insecticide', 'priority': 'last_resort', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.90},
        
        # Aphids recommendations
        {'pest': 'Aphids', 'treatment': 'Hand-picking', 'priority': 'primary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.60},
        {'pest': 'Aphids', 'treatment': 'Intercropping', 'priority': 'primary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.70},
        {'pest': 'Aphids', 'treatment': 'Sanitation and Field Hygiene', 'priority': 'primary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.72},
        {'pest': 'Aphids', 'treatment': 'Ladybugs (Coccinellidae)', 'priority': 'primary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.78},
        {'pest': 'Aphids', 'treatment': 'Neem Oil Spray', 'priority': 'secondary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.73},
        {'pest': 'Aphids', 'treatment': 'Systemic Insecticide', 'priority': 'last_resort', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.88},
        
        # Tomato Leafminer recommendations
        {'pest': 'Tomato Leafminer', 'treatment': 'Sanitation and Field Hygiene', 'priority': 'primary', 'region': 'global', 'crop_type': 'tomato', 'success_rate': 0.75},
        {'pest': 'Tomato Leafminer', 'treatment': 'Trap Crops', 'priority': 'primary', 'region': 'global', 'crop_type': 'tomato', 'success_rate': 0.70},
        {'pest': 'Tomato Leafminer', 'treatment': 'Parasitic Wasps (Trichogramma)', 'priority': 'primary', 'region': 'global', 'crop_type': 'tomato', 'success_rate': 0.82},
        {'pest': 'Tomato Leafminer', 'treatment': 'Bacillus thuringiensis (Bt) Spray', 'priority': 'secondary', 'region': 'global', 'crop_type': 'tomato', 'success_rate': 0.80},
        {'pest': 'Tomato Leafminer', 'treatment': 'Synthetic Pyrethroid Insecticide', 'priority': 'last_resort', 'region': 'global', 'crop_type': 'tomato', 'success_rate': 0.92},
        
        # Whitefly recommendations
        {'pest': 'Whitefly', 'treatment': 'Intercropping', 'priority': 'primary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.68},
        {'pest': 'Whitefly', 'treatment': 'Sanitation and Field Hygiene', 'priority': 'primary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.70},
        {'pest': 'Whitefly', 'treatment': 'Neem Oil Spray', 'priority': 'secondary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.75},
        {'pest': 'Whitefly', 'treatment': 'Entomopathogenic Nematodes', 'priority': 'secondary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.72},
        {'pest': 'Whitefly', 'treatment': 'Systemic Insecticide', 'priority': 'last_resort', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.90},
        
        # Spider Mites recommendations
        {'pest': 'Spider Mites', 'treatment': 'Sanitation and Field Hygiene', 'priority': 'primary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.70},
        {'pest': 'Spider Mites', 'treatment': 'Intercropping', 'priority': 'primary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.68},
        {'pest': 'Spider Mites', 'treatment': 'Neem Oil Spray', 'priority': 'secondary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.76},
        {'pest': 'Spider Mites', 'treatment': 'Ladybugs (Coccinellidae)', 'priority': 'secondary', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.74},
        {'pest': 'Spider Mites', 'treatment': 'Organophosphate Insecticide', 'priority': 'last_resort', 'region': 'global', 'crop_type': 'all', 'success_rate': 0.92},
    ]
    
    created_count = 0
    for rec_data in recommendations_data:
        pest = find_pest(rec_data['pest'])
        treatment = find_treatment(rec_data['treatment'])
        
        if not pest:
            logger.warning(f"Pest not found: {rec_data['pest']}")
            continue
        
        if not treatment:
            logger.warning(f"Treatment not found: {rec_data['treatment']}")
            continue
        
        # Check if recommendation already exists
        existing = IPMRecommendation.query.filter_by(
            pest_id=pest.id,
            treatment_id=treatment.id,
            region=rec_data['region']
        ).first()
        
        if existing:
            logger.info(f"Recommendation already exists: {pest.common_name} -> {treatment.name}")
            continue
        
        recommendation = IPMRecommendation(
            pest_id=pest.id,
            treatment_id=treatment.id,
            priority=rec_data['priority'],
            region=rec_data['region'],
            crop_type=rec_data.get('crop_type'),
            success_rate=rec_data.get('success_rate')
        )
        
        db.session.add(recommendation)
        created_count += 1
        logger.info(f"Added recommendation: {pest.common_name} -> {treatment.name} ({rec_data['priority']})")
    
    db.session.commit()
    logger.info(f"Created {created_count} IPM recommendations")


def main():
    """Main function to seed all IPM data"""
    with app.app_context():
        logger.info("Starting IPM database seeding...")
        
        # Seed pests
        logger.info("Seeding pests...")
        pests = seed_pests()
        logger.info(f"Seeded {len(pests)} pests")
        
        # Seed treatments
        logger.info("Seeding treatments...")
        treatments = seed_treatments()
        logger.info(f"Seeded {len(treatments)} treatments")
        
        # Seed IPM recommendations
        logger.info("Seeding IPM recommendations...")
        seed_ipm_recommendations(pests, treatments)
        
        logger.info("IPM database seeding completed successfully!")


if __name__ == '__main__':
    main()
