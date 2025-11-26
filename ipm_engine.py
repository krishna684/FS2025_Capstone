"""
IPM (Integrated Pest Management) Recommendation Engine

This module provides rule-based pest management recommendations following IPM principles:
- Cultural and biological controls prioritized first
- Chemical controls as last resort
- Regional filtering based on regulations
"""

from models import IPMRecommendation, Treatment, PestDatabase
from database import db
import logging

logger = logging.getLogger(__name__)


def query_ipm_rules(pest_id, crop=None, region=None):
    """
    Query IPM recommendations for a specific pest
    
    Args:
        pest_id: ID of the pest from PestDatabase
        crop: Optional crop type to filter recommendations
        region: Optional region code to filter recommendations
        
    Returns:
        List of IPMRecommendation objects
    """
    try:
        # Start with base query
        query = IPMRecommendation.query.filter_by(pest_id=pest_id)
        
        # Filter by region (include both specific region and 'global' recommendations)
        if region:
            query = query.filter(
                (IPMRecommendation.region == region) | 
                (IPMRecommendation.region == 'global') |
                (IPMRecommendation.region == None)
            )
        else:
            # If no region specified, only get global recommendations
            query = query.filter(
                (IPMRecommendation.region == 'global') |
                (IPMRecommendation.region == None)
            )
        
        # Filter by crop type if specified
        if crop:
            query = query.filter(
                (IPMRecommendation.crop_type == crop) |
                (IPMRecommendation.crop_type == None) |
                (IPMRecommendation.crop_type == 'all')
            )
        
        recommendations = query.all()
        logger.info(f"Found {len(recommendations)} recommendations for pest_id={pest_id}, crop={crop}, region={region}")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error querying IPM rules: {e}")
        return []


def sort_by_ipm_priority(recommendations):
    """
    Sort recommendations by IPM priority: cultural/biological first, chemical last
    
    Priority order:
    1. Cultural controls (priority='primary')
    2. Biological controls (priority='primary' or 'secondary')
    3. Chemical controls (priority='last_resort')
    
    Args:
        recommendations: List of IPMRecommendation objects
        
    Returns:
        Sorted list of IPMRecommendation objects
    """
    # Define priority weights for sorting
    priority_weights = {
        'primary': 1,
        'secondary': 2,
        'last_resort': 3
    }
    
    # Define type weights (cultural/biological before chemical)
    type_weights = {
        'cultural': 1,
        'biological': 2,
        'chemical': 3
    }
    
    def sort_key(rec):
        # Get priority weight (default to secondary if not specified)
        priority_weight = priority_weights.get(rec.priority, 2)
        
        # Get treatment type weight
        treatment_type = rec.treatment.type if rec.treatment else 'unknown'
        type_weight = type_weights.get(treatment_type, 4)
        
        # Sort by type first, then priority, then success rate (descending)
        success_rate = rec.success_rate if rec.success_rate else 0
        return (type_weight, priority_weight, -success_rate)
    
    sorted_recs = sorted(recommendations, key=sort_key)
    logger.info(f"Sorted {len(sorted_recs)} recommendations by IPM priority")
    
    return sorted_recs


def filter_by_regulations(recommendations, region):
    """
    Filter recommendations based on regional regulations
    
    This is a placeholder for regulatory filtering. In production, this would
    integrate with external regulatory databases (USDA IPM, local ag ministry APIs)
    
    Args:
        recommendations: List of IPMRecommendation objects
        region: Region code for regulatory filtering
        
    Returns:
        Filtered list of IPMRecommendation objects with regulatory annotations
    """
    # For MVP, we'll implement basic filtering logic
    # In production, this would query external regulatory databases
    
    filtered_recs = []
    
    # Define prohibited treatments by region (example data)
    # In production, this would come from a database or external API
    prohibited_treatments = {
        'US_CA': ['DDT', 'Chlordane'],  # California prohibitions
        'EU': ['Neonicotinoids', 'Chlorpyrifos'],  # EU prohibitions
        'East_Africa': ['Paraquat'],  # East Africa prohibitions
    }
    
    # Define restricted treatments (require special permits)
    restricted_treatments = {
        'US_CA': ['Methyl Bromide'],
        'EU': ['Glyphosate'],
    }
    
    prohibited = prohibited_treatments.get(region, [])
    restricted = restricted_treatments.get(region, [])
    
    for rec in recommendations:
        treatment_name = rec.treatment.name if rec.treatment else ''
        
        # Check if treatment is prohibited
        is_prohibited = any(p.lower() in treatment_name.lower() for p in prohibited)
        
        if is_prohibited:
            logger.info(f"Filtered out prohibited treatment: {treatment_name} in region {region}")
            continue
        
        # Check if treatment is restricted
        is_restricted = any(r.lower() in treatment_name.lower() for r in restricted)
        
        if is_restricted:
            # Add annotation for restricted treatment
            rec.regulatory_note = f"Restricted in {region}. Special permit may be required."
            logger.info(f"Annotated restricted treatment: {treatment_name} in region {region}")
        
        filtered_recs.append(rec)
    
    logger.info(f"Filtered {len(recommendations)} recommendations to {len(filtered_recs)} for region {region}")
    
    return filtered_recs


def annotate_chemical_treatments(recommendations):
    """
    Add "Last Resort" labels and safety warnings to chemical treatments
    
    Args:
        recommendations: List of IPMRecommendation objects
        
    Returns:
        List of IPMRecommendation objects with annotations
    """
    for rec in recommendations:
        if rec.treatment and rec.treatment.type == 'chemical':
            # Mark as last resort
            rec.is_last_resort = True
            
            # Add safety warning
            rec.safety_warning = (
                "⚠️ CHEMICAL TREATMENT - USE AS LAST RESORT ONLY. "
                "Follow all label instructions. Wear protective equipment. "
                "Observe re-entry intervals. Consider environmental impact."
            )
            
            # Add visual indicator
            rec.warning_icon = "⚠️"
            
            logger.debug(f"Annotated chemical treatment: {rec.treatment.name}")
    
    return recommendations


def get_recommendations(pest_id, crop=None, region=None, language='en'):
    """
    Main function to get IPM recommendations for a pest
    
    This function orchestrates the complete recommendation pipeline:
    1. Query rule base
    2. Sort by IPM priority
    3. Filter by regional regulations
    4. Annotate chemical treatments
    
    Args:
        pest_id: ID of the pest from PestDatabase
        crop: Optional crop type
        region: Optional region code
        language: Language code for localized descriptions (default: 'en')
        
    Returns:
        List of dictionaries with recommendation details
    """
    try:
        # Step 1: Query rule base
        recommendations = query_ipm_rules(pest_id, crop, region)
        
        if not recommendations:
            logger.warning(f"No recommendations found for pest_id={pest_id}")
            return []
        
        # Step 2: Sort by IPM priority
        recommendations = sort_by_ipm_priority(recommendations)
        
        # Step 3: Filter by regional regulations
        if region:
            recommendations = filter_by_regulations(recommendations, region)
        
        # Step 4: Annotate chemical treatments
        recommendations = annotate_chemical_treatments(recommendations)
        
        # Step 5: Format output
        result = []
        for rec in recommendations:
            treatment = rec.treatment
            if not treatment:
                continue
            
            # Get localized description
            desc_field = f'description_{language}'
            localized_desc = getattr(treatment, desc_field, None) if language != 'en' else None
            description = localized_desc or treatment.description
            
            rec_dict = {
                'id': rec.id,
                'treatment_name': treatment.name,
                'type': treatment.type,
                'description': description,
                'priority': rec.priority,
                'cost_estimate': treatment.cost_estimate,
                'effectiveness_rate': treatment.effectiveness_rate,
                'success_rate': rec.success_rate,
                'is_last_resort': getattr(rec, 'is_last_resort', False),
                'safety_warning': getattr(rec, 'safety_warning', None),
                'warning_icon': getattr(rec, 'warning_icon', None),
                'regulatory_note': getattr(rec, 'regulatory_note', None)
            }
            
            result.append(rec_dict)
        
        logger.info(f"Returning {len(result)} recommendations for pest_id={pest_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return []


def get_pest_by_name(pest_name, language='en'):
    """
    Helper function to get pest ID by name
    
    Args:
        pest_name: Common name of the pest
        language: Language code for localized search
        
    Returns:
        PestDatabase object or None
    """
    try:
        # Try exact match first
        pest = PestDatabase.query.filter_by(common_name=pest_name).first()
        
        if not pest and language != 'en':
            # Try localized name
            name_field = f'name_{language}'
            pest = PestDatabase.query.filter(
                getattr(PestDatabase, name_field) == pest_name
            ).first()
        
        if not pest:
            # Try case-insensitive partial match
            pest = PestDatabase.query.filter(
                PestDatabase.common_name.ilike(f'%{pest_name}%')
            ).first()
        
        return pest
        
    except Exception as e:
        logger.error(f"Error finding pest by name: {e}")
        return None
