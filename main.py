from telegram import Update
from telegram.ext import Application
from config import TELEGRAM_TOKEN
from telegram_handlers import setup_handlers
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Create the Application
    logger.info("Starting Sports Buddy Bot")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Set up all handlers
    setup_handlers(application)
    logger.info("Handlers initialized")

    # Start the Bot
    logger.info("Bot is polling for updates")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()