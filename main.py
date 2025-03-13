from telegram import Update
from telegram.ext import Application
from config import TELEGRAM_TOKEN
from telegram_handlers import setup_handlers
import logging
import os
import asyncio
from aiohttp import web

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

async def health_check(request):
    return web.Response(text="Bot is running!")

async def start_health_server():
    """Start a web server for health checks"""
    app = web.Application()
    app.router.add_get("/", health_check)  # Root path for simplicity
    app.router.add_get("/health", health_check)

    # Get port from environment variable or use default
    PORT = int(os.environ.get("PORT", 8080))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

    logger.info(f"Health check server started on port {PORT}")

    # Keep the server running
    while True:
        await asyncio.sleep(3600)  # Keep the task alive

if __name__ == "__main__":
    main()