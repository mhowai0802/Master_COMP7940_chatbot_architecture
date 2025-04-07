import configparser
import os
from pathlib import Path

# Read config file
config = configparser.ConfigParser()
config_file = Path(__file__).parent / "config.ini"
config.read(config_file)

# ChatGPT API configuration
CHATGPT_BASIC_URL = config.get('CHATGPT', 'BASICURL')
CHATGPT_MODEL_NAME = config.get('CHATGPT', 'MODELNAME')
CHATGPT_API_VERSION = config.get('CHATGPT', 'APIVERSION')
CHATGPT_ACCESS_TOKEN = config.get('CHATGPT', 'ACCESS_TOKEN')

# Telegram configuration
TELEGRAM_TOKEN = config.get('TELEGRAM', 'TOKEN')

# MongoDB configuration
MONGODB_URI = config.get('MONGODB', 'URI')
MONGODB_DB_NAME = config.get('MONGODB', 'DB_NAME')