from datetime import datetime
from pymongo import MongoClient
import logging
from config import MONGODB_URI, MONGODB_DB_NAME

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    sports_collection = db['sports_activities']
    # Create an index on date for faster queries
    sports_collection.create_index('date')
    logger.info(f"Connected to MongoDB successfully at {MONGODB_URI}")
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {e}")


    # Provide a fallback for testing
    class FallbackDB:
        def __init__(self):
            self.sports_activities = []

        def insert_one(self, document):
            self.sports_activities.append(document)
            return True

        def find(self, query=None):
            today = datetime.now().strftime("%Y-%m-%d")
            if query and 'date' in query:
                return [activity for activity in self.sports_activities if activity['date'] == query['date']]
            return self.sports_activities

        def count_documents(self, query=None):
            if not query:
                return len(self.sports_activities)

            count = 0
            for doc in self.sports_activities:
                match = True
                for k, v in query.items():
                    if k not in doc or doc[k] != v:
                        match = False
                        break
                if match:
                    count += 1
            return count

        def distinct(self, field):
            result = set()
            for doc in self.sports_activities:
                if field in doc:
                    result.add(doc[field])
            return list(result)


    sports_collection = FallbackDB()
    logger.warning("Using fallback in-memory database")


def save_sport_now(sport_info, user_name):
    """
    Save sport activity information to the database.

    Args:
        sport_info (dict): Dictionary containing sport details
            Required keys: sport, datetime, location, district, date
        user_name (str): Name of the user registering the activity

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Add additional metadata
        document = sport_info.copy()
        document['name'] = user_name
        document['created_at'] = datetime.now()

        # Insert into database
        result = sports_collection.insert_one(document)
        logger.info(f"Saved sport activity: {sport_info['sport']} by {user_name}")
        return True
    except Exception as e:
        logger.error(f"Error saving sport activity: {e}")
        return False


def find_sport_buddies(sport=None, district=None):
    """
    Find people playing sports today.

    Args:
        sport (str, optional): Filter by specific sport
        district (str, optional): Filter by specific district

    Returns:
        list: List of sport activities matching the criteria
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

    Args:
        message (str): User message text

    Returns:
        dict: Extracted sport information
    """
    # This is a simple implementation.
    # In a real application, you would use more sophisticated NLP or
    # your GPT router to extract this information more accurately.

    sport_info = {}

    # Try to extract sport
    common_sports = ["basketball", "football", "soccer", "tennis", "badminton",
                     "running", "swimming", "volleyball", "table tennis"]
    for sport in common_sports:
        if sport in message.lower():
            sport_info['sport'] = sport.title()
            break

    # Simple time extraction
    time_indicators = ["at ", "from ", "starting at ", "begin at "]
    for indicator in time_indicators:
        if indicator in message.lower():
            # Extract time (very simplified)
            parts = message.lower().split(indicator)
            if len(parts) > 1:
                time_part = parts[1].split()[0]
                sport_info['datetime'] = time_part
                break

    # Simple location extraction (look for "in" or "at")
    location_indicators = [" in ", " at "]
    for indicator in location_indicators:
        if indicator in message:
            parts = message.split(indicator)
            if len(parts) > 1:
                location_part = parts[1].split(".")[0]  # Until period or end
                sport_info['location'] = location_part.strip()
                break

    # Default values if not found
    if 'sport' not in sport_info:
        sport_info['sport'] = "Unknown Sport"
    if 'datetime' not in sport_info:
        sport_info['datetime'] = datetime.now().strftime("%H:%M")
    if 'location' not in sport_info:
        sport_info['location'] = "Unknown Location"

    # Add today's date
    sport_info['date'] = datetime.now().strftime("%Y-%m-%d")

    # Extract district if mentioned, otherwise set to Unknown
    if 'location' in sport_info:
        # Simplified district extraction
        hk_districts = ["central", "wan chai", "causeway bay", "north point",
                        "tsim sha tsui", "mong kok", "sham shui po", "sha tin",
                        "tai po", "tuen mun"]
        for district in hk_districts:
            if district in sport_info['location'].lower():
                sport_info['district'] = district.title()
                break
        if 'district' not in sport_info:
            sport_info['district'] = "Unknown District"

    return sport_info


def get_recent_activities(limit=5):
    """
    Get the most recent sport activities.

    Args:
        limit (int): Maximum number of activities to return

    Returns:
        list: List of recent sport activities
    """
    try:
        # Sort by created_at in descending order (newest first)
        results = list(sports_collection.find().sort('created_at', -1).limit(limit))

        # Remove MongoDB _id field for each result
        for result in results:
            if '_id' in result:
                del result['_id']

        logger.info(f"Retrieved {len(results)} recent sport activities")
        return results
    except Exception as e:
        logger.error(f"Error getting recent activities: {e}")
        return []


def get_activity_stats():
    """
    Get statistics about sport activities.

    Returns:
        dict: Statistics about sport activities
    """
    try:
        # Count total activities
        total = sports_collection.count_documents({})

        # Count activities by sport
        sports = {}
        for sport in sports_collection.distinct('sport'):
            count = sports_collection.count_documents({'sport': sport})
            sports[sport] = count

        # Count activities by district
        districts = {}
        for district in sports_collection.distinct('district'):
            count = sports_collection.count_documents({'district': district})
            districts[district] = count

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