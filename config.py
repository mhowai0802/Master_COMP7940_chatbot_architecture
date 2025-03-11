import configparser
import logging
import pymongo
from HKBU_ChatGPT import HKBU_ChatGPT

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = configparser.ConfigParser()
config.read('./config.ini')

# Initialize ChatGPT
chatgpt = HKBU_ChatGPT('./config.ini')

# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["project"]
sport_now_collection = db["sport_now"]

# Get Telegram token
TELEGRAM_TOKEN = config['TELEGRAM']['TOKEN']