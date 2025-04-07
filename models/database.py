import logging
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pymongo.server_api import ServerApi

from config import MONGODB_URI, MONGODB_DB_NAME

logger = logging.getLogger(__name__)

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
            self.db = self.client[MONGODB_DB_NAME]
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