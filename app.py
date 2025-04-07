import logging
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, CommandHandler, CallbackQueryHandler, Filters
import os
from config import TELEGRAM_TOKEN
from handlers.message_handlers import (
    start, help_command, sport_now_command,
    find_sport_buddy, stats_command, handle_message,
    handle_callback_query, clear_chat
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize app
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

# Register handlers
handlers = {
    "start": start,
    "help": help_command,
    "sport_now": sport_now_command,
    "find_sport_buddy": find_sport_buddy,
    "stats": stats_command,
    "clear": clear_chat
}

for command, handler in handlers.items():
    dispatcher.add_handler(CommandHandler(command, handler))

# Add callback query handler first to ensure it gets priority
dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))

# Then add message handler
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))


@app.route('/')
def health():
    return jsonify({"status": "healthy"})


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        logger.info(f"Webhook received data: {data}")

        update = Update.de_json(data, bot)

        # Check if this is a callback query for debugging
        if hasattr(update, 'callback_query') and update.callback_query:
            logger.info(f"Processing callback query: {update.callback_query.data}")

        dispatcher.process_update(update)
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/set_webhook')
def set_webhook():
    url = request.args.get('url', '')
    if not url:
        return "Please provide a URL parameter", 400

    webhook_url = f"{url}/webhook"
    try:
        bot.delete_webhook()
        success = bot.set_webhook(webhook_url)
        return jsonify({
            "success": success,
            "webhook_url": webhook_url
        })
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)