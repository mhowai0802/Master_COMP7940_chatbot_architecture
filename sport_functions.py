from datetime import datetime
import logging
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pymongo.server_api import ServerApi
from config import MONGODB_URI, MONGODB_DB_NAME

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# MongoDB connection class
class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.activities_collection = None
        self.is_available = self._connect()

    def _connect(self):
        try:
            self.client = MongoClient(MONGODB_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
            self.client.admin.command('ping')  # Force a connection to verify it works
            self.db = self.client["sport_buddy_db"]
            self.activities_collection = self.db["activities"]
            logger.info("MongoDB connection successful")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error: {str(e)}")
            return False

    def get_collection(self):
        if self.is_available:
            return self.activities_collection
        else:
            return FallbackDB()


# Define a fallback database class
class FallbackDB:
    def __init__(self):
        self.sports_activities = []
        logger.warning("Using fallback in-memory database")

    def insert_one(self, document):
        self.sports_activities.append(document)
        return type('obj', (object,), {'inserted_id': True})

    def find(self, query=None):
        return Cursor(self.sports_activities, query)

    def count_documents(self, query=None):
        if not query:
            return len(self.sports_activities)

        count = 0
        for doc in self.sports_activities:
            if self._matches_query(doc, query):
                count += 1
        return count

    def distinct(self, field):
        result = set()
        for doc in self.sports_activities:
            if field in doc:
                result.add(doc[field])
        return list(result)

    def _matches_query(self, document, query):
        if not query:
            return True

        for k, v in query.items():
            if k not in document or document[k] != v:
                return False
        return True


class Cursor:
    def __init__(self, activities, query=None):
        self.activities = activities
        self.query = query or {}
        self.sort_field = None
        self.sort_direction = 1
        self.limit_val = None

    def sort(self, field, direction):
        self.sort_field = field
        self.sort_direction = direction
        return self

    def limit(self, limit_val):
        self.limit_val = limit_val
        return self

    def __iter__(self):
        results = []
        for activity in self.activities:
            match = True
            for k, v in self.query.items():
                if k not in activity or activity[k] != v:
                    match = False
                    break
            if match:
                results.append(activity)

        if self.sort_field:
            results.sort(key=lambda x: x.get(self.sort_field, ''), reverse=(self.sort_direction == -1))

        if self.limit_val:
            results = results[:self.limit_val]

        return iter(results)


# Initialize database
db = Database()
sports_collection = db.get_collection()


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
        sports_collection.insert_one(document)
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