import logging
from datetime import datetime

from models.database import sports_collection

logger = logging.getLogger(__name__)

def save_sport_now(sport_info, user_name):
    """
    Save sport activity information to the database.
    """
    try:
        # Add additional metadata
        document = sport_info.copy()
        document['name'] = user_name
        document['created_at'] = datetime.now()

        # Insert into database
        sports_collection.insert_one(document)
        logger.info(f"Saved sport activity: {sport_info['sport']} by {user_name}")
        return True
    except Exception as e:
        logger.error(f"Error saving sport activity: {e}")
        return False


def find_sport_buddies(sport=None, district=None):
    """
    Find people playing sports today.
    """
    try:
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")

        # Build query
        query = {'date': today}
        if sport:
            query['sport'] = sport
        if district:
            query['district'] = district

        # Find matching activities
        results = list(sports_collection.find(query))

        # Remove MongoDB _id field for each result
        for result in results:
            if '_id' in result:
                del result['_id']

        logger.info(f"Found {len(results)} sport activities for today")
        return results
    except Exception as e:
        logger.error(f"Error finding sport buddies: {e}")
        return []


def extract_sport_now_info(message):
    """
    Extract sport details from a user message (fallback method).
    """
    sport_info = {
        'sport': "Unknown Sport",
        'datetime': datetime.now().strftime("%H:%M"),
        'location': "Unknown Location",
        'district': "Unknown District",
        'date': datetime.now().strftime("%Y-%m-%d")
    }

    # Try to extract sport
    common_sports = ["basketball", "football", "soccer", "tennis", "badminton",
                     "running", "swimming", "volleyball", "table tennis"]
    for sport in common_sports:
        if sport in message.lower():
            sport_info['sport'] = sport.title()
            break

    # Simple time extraction
    for indicator in ["at ", "from ", "starting at ", "begin at "]:
        if indicator in message.lower():
            parts = message.lower().split(indicator)
            if len(parts) > 1:
                time_part = parts[1].split()[0]
                sport_info['datetime'] = time_part
                break

    # Simple location extraction
    for indicator in [" in ", " at "]:
        if indicator in message:
            parts = message.split(indicator)
            if len(parts) > 1:
                location_part = parts[1].split(".")[0]  # Until period or end
                sport_info['location'] = location_part.strip()
                break

    # Extract district if mentioned
    hk_districts = ["central", "wan chai", "causeway bay", "north point",
                    "tsim sha tsui", "mong kok", "sham shui po", "sha tin",
                    "tai po", "tuen mun"]
    for district in hk_districts:
        if district in sport_info['location'].lower():
            sport_info['district'] = district.title()
            break

    return sport_info


def get_activity_stats():
    """
    Get statistics about sport activities.
    """
    try:
        # Count total activities
        total = sports_collection.count_documents({})

        # Count activities by sport and district
        sports = {}
        districts = {}

        for sport in sports_collection.distinct('sport'):
            sports[sport] = sports_collection.count_documents({'sport': sport})

        for district in sports_collection.distinct('district'):
            districts[district] = sports_collection.count_documents({'district': district})

        # Get today's count
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = sports_collection.count_documents({'date': today})

        stats = {
            'total': total,
            'sports': sports,
            'districts': districts,
            'today_count': today_count
        }

        logger.info(f"Retrieved activity stats: {total} total activities")
        return stats
    except Exception as e:
        logger.error(f"Error getting activity stats: {e}")
        return {'total': 0, 'sports': {}, 'districts': {}, 'today_count': 0}