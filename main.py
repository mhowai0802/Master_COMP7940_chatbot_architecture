import os
import logging
import sys
import asyncio
from aiohttp import web
from telegram.ext import Application
from telegram_handlers import setup_handlers
from config import TELEGRAM_TOKEN

# Configure logging for containerized environment
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout  # Log to stdout for container logs
)
logger = logging.getLogger(__name__)


# Create a simple health check endpoint
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


async def start_bot():
    """Start the Telegram bot"""
    # Create the Application with proper shutdown signals
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Setup all handlers
    setup_handlers(application)

    # Run the bot using polling
    await application.run_polling(allowed_updates=Application.ALL_UPDATES)


def main() -> None:
    """Start both the bot and the health server"""
    # Check if token is available
    if not TELEGRAM_TOKEN:
        logger.error("No TELEGRAM_TOKEN provided. Set this environment variable and restart.")
        sys.exit(1)

    # Run both the bot and the health server
    logger.info("Starting Sports Buddy Bot...")

    # Use asyncio to run both servers
    loop = asyncio.get_event_loop()

    # Create tasks for both servers
    tasks = [
        loop.create_task(start_health_server()),
        loop.create_task(start_bot())
    ]

    # Run until complete
    loop.run_until_complete(asyncio.gather(*tasks))


if __name__ == "__main__":
    main()