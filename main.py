import os
import logging
import sys
import threading
from flask import Flask
from telegram.ext import Application
from telegram_handlers import setup_handlers
from config import TELEGRAM_TOKEN

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def start_bot():
    """Start the Telegram bot in a separate thread"""
    # Check if token is available
    if not TELEGRAM_TOKEN:
        logger.error("No TELEGRAM_TOKEN provided. Set this environment variable and restart.")
        return

    logger.info("Starting Sports Buddy Bot...")
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Setup all handlers
    setup_handlers(application)

    # Run the bot
    application.run_polling()


if __name__ == "__main__":
    # Start the bot in a separate thread
    start_bot()