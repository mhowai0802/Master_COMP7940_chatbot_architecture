import asyncio
from datetime import datetime
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

from sport_functions import save_sport_now, find_sport_buddies, get_activity_stats
from gpt_router import GPTRouter

# Set up logging
logger = logging.getLogger(__name__)

# Initialize GPT router
gpt_router = GPTRouter()

# Define conversation states for sport registration
SPORT, LOCATION, DISTRICT, TIME, CONFIRMATION = range(5)

# Common sports list for quick selection
COMMON_SPORTS = ["Basketball", "Football", "Tennis", "Badminton", "Running",
                 "Swimming", "Volleyball", "Table Tennis"]

# Districts in Hong Kong for quick selection
HK_DISTRICTS = ["Central", "Wan Chai", "Causeway Bay", "North Point", "Quarry Bay",
                "Tsim Sha Tsui", "Mong Kok", "Yau Ma Tei", "Sham Shui Po",
                "Sha Tin", "Tai Po", "Tuen Mun", "Yuen Long", "Tsuen Wan"]


# Helper functions to create keyboards
def create_grid_keyboard(items, prefix, buttons_per_row=2, add_other=True):
    """Create a grid keyboard from a list of items."""
    keyboard = []
    row = []

    for i, item in enumerate(items):
        row.append(InlineKeyboardButton(item, callback_data=f"{prefix}_{item}"))
        if (i + 1) % buttons_per_row == 0 or i == len(items) - 1:
            keyboard.append(row)
            row = []

    if add_other:
        keyboard.append([InlineKeyboardButton(f"Other {prefix.title()}", callback_data=f"{prefix}_other")])

    return InlineKeyboardMarkup(keyboard)


def create_time_keyboard(current_hour):
    """Create a keyboard with time suggestions starting from current hour."""
    keyboard = []
    time_suggestions = []

    for hour in range(current_hour, min(current_hour + 8, 23)):
        time_suggestions.append(f"{hour}:00")
        time_suggestions.append(f"{hour}:30")

    row = []
    for i, time in enumerate(time_suggestions):
        row.append(InlineKeyboardButton(time, callback_data=f"time_{time}"))
        if (i + 1) % 3 == 0 or i == len(time_suggestions) - 1:
            keyboard.append(row)
            row = []

    keyboard.append([InlineKeyboardButton("Other Time", callback_data="time_other")])
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a friendly welcome message when the command /start is issued."""
    user = update.effective_user
    first_name = user.first_name

    welcome_message = (
        f"Hey {first_name}! 👋 Great to meet you!\n\n"
        f"I'm your Sports Buddy, here to help you connect with other sports enthusiasts. "
        f"So tell me, what brings you here today?\n\n"
        f"Are you looking to play a sport right now and want to let others know? Or maybe "
        f"you're trying to find some friends to join you for a game?\n\n"
        f"You can just chat with me naturally or use commands like /sport_now or /find_sport_buddy to get started!"
    )

    await update.message.reply_text(welcome_message)

    # After a short delay, follow up with a prompt
    await asyncio.sleep(1)
    await update.message.reply_text("So, what's your sports plan for today? Ready to play or looking for teammates?")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    try:
        help_text = (
            "🏆 *Sports Buddy Bot Help* 🏆\n\n"
            "*Available Commands:*\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/sport_now - Register that you're playing a sport now\n"
            "/find_sport_buddy - Find people to play sports with\n"
            "/stats - View activity statistics\n"
            "/clear - Clear the chat history\n\n"
            "You can also just chat with me naturally about your sports plans!"
        )
        logger.info(f"Sending help message to user {update.effective_user.id}")
        await update.message.reply_text(help_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in help_command: {str(e)}")
        # Fallback to plain text if Markdown fails
        await update.message.reply_text(
            "Sports Buddy Bot Help\n\n"
            "Available Commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/sport_now - Register that you're playing a sport now\n"
            "/find_sport_buddy - Find people to play sports with\n"
            "/stats - View activity statistics\n"
            "/clear - Clear the chat history\n\n"
            "You can also just chat with me naturally about your sports plans!"
        )

async def sport_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the sport now registration process"""
    user = update.effective_user
    context.user_data['name'] = user.first_name  # Automatically use their Telegram name

    # Log the entry to conversation
    logger.info(f"User {user.first_name} ({user.id}) started sport registration")

    # Create keyboard with common sports
    reply_markup = create_grid_keyboard(COMMON_SPORTS, "sport", 2)

    await update.message.reply_text(
        f"Hi {user.first_name}! Let's register your sport activity for today.\n\n"
        f"What sport will you be playing?",
        reply_markup=reply_markup
    )

    return SPORT


async def sport_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle sport selection"""
    query = update.callback_query
    await query.answer()

    # Log the callback
    logger.info(f"Received sport choice callback: {query.data}")

    choice = query.data.replace("sport_", "")

    if choice == "other":
        await query.message.edit_text("Please type the name of the sport you'll be playing:")
        return SPORT
    else:
        context.user_data['sport'] = choice
        logger.info(f"User selected sport: {choice}")

        # Now ask for location
        await query.message.edit_text(
            f"Great! You'll be playing {choice}. What's the specific location?\n"
            f"(e.g., Victoria Park Basketball Court, HKBU Sports Centre)"
        )
        return LOCATION


async def location_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location input"""
    # Different handling based on whether this is a callback or text message
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        # Extract sport from callback_data
        sport = query.data.replace("sport_", "")
        context.user_data['sport'] = sport
        logger.info(f"User selected sport via callback: {sport}")

        await query.message.edit_text(
            f"Great! You'll be playing {sport}. What's the specific location?\n"
            f"(e.g., Victoria Park Basketball Court, HKBU Sports Centre)"
        )
        return LOCATION
    else:
        # Handle text input
        text = update.message.text
        logger.info(f"Received text in location_input: {text}")

        if 'sport' not in context.user_data:
            # This is a sport input
            context.user_data['sport'] = text
            logger.info(f"Set sport from text: {text}")

            await update.message.reply_text(
                f"Great! You'll be playing {text}. What's the specific location?\n"
                f"(e.g., Victoria Park Basketball Court, HKBU Sports Centre)"
            )
            return LOCATION
        else:
            # This is a location input
            context.user_data['location'] = text
            logger.info(f"Set location: {text}")

            # Create district selection keyboard
            reply_markup = create_grid_keyboard(HK_DISTRICTS, "district", 3)

            await update.message.reply_text("Which district is this in?", reply_markup=reply_markup)
            return DISTRICT


async def district_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle district selection"""
    query = update.callback_query
    await query.answer()

    logger.info(f"Received district choice callback: {query.data}")

    choice = query.data.replace("district_", "")

    if choice == "other":
        await query.message.edit_text("Please type the name of the district:")
        return DISTRICT
    else:
        context.user_data['district'] = choice
        logger.info(f"Set district: {choice}")

        # Create time suggestion keyboard
        current_hour = datetime.now().hour
        reply_markup = create_time_keyboard(current_hour)

        await query.message.edit_text("What time will you be playing today?", reply_markup=reply_markup)
        return TIME


async def district_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle text input for district"""
    text = update.message.text
    context.user_data['district'] = text
    logger.info(f"Set district from text: {text}")

    # Create time suggestion keyboard
    current_hour = datetime.now().hour
    reply_markup = create_time_keyboard(current_hour)

    await update.message.reply_text("What time will you be playing today?", reply_markup=reply_markup)
    return TIME


async def time_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle time selection"""
    query = update.callback_query
    await query.answer()

    logger.info(f"Received time choice callback: {query.data}")

    choice = query.data.replace("time_", "")

    if choice == "other":
        await query.message.edit_text("Please enter the time (e.g., 14:30, 2:30 PM):")
        return TIME
    else:
        context.user_data['time'] = choice
        logger.info(f"Set time from callback: {choice}")

        # Call show_confirmation directly with the message object
        await show_confirmation(query.message, context)
        return CONFIRMATION


async def time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle text input for time"""
    text = update.message.text
    context.user_data['time'] = text
    logger.info(f"Set time from text: {text}")

    # Call show_confirmation with the message object
    await show_confirmation(update.message, context)
    return CONFIRMATION


async def show_confirmation(message, context) -> int:
    """Show confirmation of all details"""
    data = context.user_data

    logger.info(f"Showing confirmation with data: {data}")

    confirmation_text = (
        f"📋 *Sport Activity Registration*\n\n"
        f"👤 *Name:* {data['name']}\n"
        f"🏀 *Sport:* {data['sport']}\n"
        f"📍 *Location:* {data['location']}\n"
        f"🏙️ *District:* {data['district']}\n"
        f"🕒 *Time:* {data['time']}\n\n"
        f"Does this look correct?"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="confirm_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(confirmation_text, reply_markup=reply_markup, parse_mode='Markdown')
    return CONFIRMATION


async def confirm_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation choice"""
    query = update.callback_query
    await query.answer()

    logger.info(f"Received confirmation callback: {query.data}")

    choice = query.data.replace("confirm_", "")

    if choice == "yes":
        # Format the data for the database
        user = update.effective_user
        sport_info = {
            'sport': context.user_data['sport'],
            'location': context.user_data['location'],
            'district': context.user_data['district'],
            'datetime': context.user_data['time'],
            'date': datetime.now().strftime("%Y-%m-%d")
        }

        # Save to database
        try:
            if save_sport_now(sport_info, user.first_name):
                await query.message.edit_text(
                    f"✅ Great! Your activity has been registered.\n\n"
                    f"I'll let others know you're playing {sport_info['sport']} at "
                    f"{sport_info['datetime']} in {sport_info['location']}.\n\n"
                    f"Have fun playing! 🎉"
                )
            else:
                await query.message.edit_text(
                    "Sorry, there was an error saving your information. Please try again."
                )
        except Exception as e:
            logger.error(f"Error saving sport activity: {str(e)}")
            await query.message.edit_text(
                "Sorry, there was an error saving your information. Please try again."
            )
    else:
        await query.message.edit_text("Registration cancelled. Feel free to try again when you're ready!")

    # Clear user data
    context.user_data.clear()
    logger.info("Conversation ended, user data cleared")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("Registration cancelled. Feel free to try again!")
    context.user_data.clear()
    logger.info("Conversation cancelled by user")
    return ConversationHandler.END


async def find_sport_buddy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help find sport buddies."""
    results = find_sport_buddies()

    if not results:
        await update.message.reply_text(
            "Sorry, I couldn't find anyone playing sports right now. Be the first by using /sport_now!"
        )
        return

    response = "Here are people playing sports today:\n\n"
    for result in results:
        response += (f"- {result['name']} is playing {result['sport']} at {result['datetime']} "
                     f"in {result['location']} ({result['district']})\n\n")

    response += "Send them a message to join!"
    await update.message.reply_text(response)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show statistics about sport activities."""
    stats = get_activity_stats()

    # Format the statistics message
    message = f"📊 *Sports Activity Statistics*\n\n"
    message += f"Total activities recorded: {stats['total']}\n"
    message += f"Activities today: {stats['today_count']}\n\n"

    if stats['sports']:
        message += "*Most popular sports:*\n"
        sorted_sports = sorted(stats['sports'].items(), key=lambda x: x[1], reverse=True)
        for sport, count in sorted_sports[:5]:  # Top 5
            message += f"- {sport}: {count} activities\n"
        message += "\n"

    if stats['districts']:
        message += "*Most active districts:*\n"
        sorted_districts = sorted(stats['districts'].items(), key=lambda x: x[1], reverse=True)
        for district, count in sorted_districts[:5]:  # Top 5
            message += f"- {district}: {count} activities\n"

    await update.message.reply_text(message, parse_mode='Markdown')


async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the chat history by sending a special message."""
    user = update.effective_user

    # Create a keyboard with confirmation buttons
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, clear chat", callback_data="clear_chat_confirm"),
            InlineKeyboardButton("❌ No, keep history", callback_data="clear_chat_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Are you sure you want to clear our chat history, {user.first_name}?",
        reply_to_message_id=update.message.message_id,
        reply_markup=reply_markup
    )


async def handle_clear_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the callback from clear chat confirmation."""
    query = update.callback_query
    await query.answer()

    if query.data == "clear_chat_confirm":
        # Delete the confirmation message
        await query.message.delete()

        # Send the cleared message
        cleared_message = (
            "🧹 Chat cleared! 🧹\n\n"
            "I've reset our conversation. Let's start fresh!\n\n"
            "What would you like to do now?\n"
            "• Use /sport_now to register a sport activity\n"
            "• Use /find_sport_buddy to find sports partners\n"
            "• Just chat with me about your sports interests"
        )
        await context.bot.send_message(chat_id=query.message.chat_id, text=cleared_message)

        # Clear any user data
        if hasattr(context, 'user_data'):
            context.user_data.clear()

        logger.info(f"Chat cleared for user {update.effective_user.id}")
    else:
        await query.message.edit_text("Chat history will be kept. Continue our conversation!")


async def handle_natural_sport_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle natural language input about wanting to play a sport"""
    message = update.message.text
    user = update.effective_user

    logger.info(f"Processing natural sport input: {message}")

    # Extract sport from message if possible
    sport_detected = None
    for sport in COMMON_SPORTS:
        if sport.lower() in message.lower():
            sport_detected = sport
            break

    if not sport_detected:
        sport_detected = "Basketball"  # Default fallback

    # Set up the context with what we know
    context.user_data['name'] = user.first_name
    context.user_data['sport'] = sport_detected

    logger.info(f"Detected sport from natural language: {sport_detected}")

    # Ask for location
    await update.message.reply_text(
        f"Great! I see you want to play {sport_detected}. What's the specific location?\n"
        f"(e.g., Victoria Park Basketball Court, HKBU Sports Centre)"
    )

    return LOCATION


async def process_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process text messages with intent routing using GPT."""
    message = update.message.text
    user = update.effective_user

    # Log the incoming message
    logger.info(f"Received message from {user.first_name} ({user.id}): {message[:50]}...")

    # Send typing action to show the bot is processing
    await update.message.chat.send_action('typing')

    try:
        # Get intent from GPT router
        intent_data = gpt_router.route_intent(message)
        logger.info(f"Intent detection result: {intent_data}")

        # Handle based on intent
        if intent_data.get('intent') == 'sport_now':
            logger.info("Detected sport_now intent, starting sport registration")
            # Start the sport_now conversation handler
            return await handle_natural_sport_input(update, context)

        elif intent_data.get('intent') == 'find_buddy':
            # They want to find sport buddies
            await find_sport_buddy(update, context)
        else:
            # For any other intent, treat as a general question about sports
            response = gpt_router.get_sport_response(message)
            await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        await update.message.reply_text(
            "Sorry, I'm having a bit of trouble right now. Please try again or use one of my commands like /sport_now or /find_sport_buddy."
        )


def setup_handlers(application):
    """Set up all the handlers for the application."""
    # Basic command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("find_sport_buddy", find_sport_buddy))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("clear", clear_chat))

    # Sport Now conversation handler - with two entry points
    sport_now_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("sport_now", sport_now),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_natural_sport_input)
        ],
        states={
            SPORT: [
                CallbackQueryHandler(sport_choice, pattern=r"^sport_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, location_input)
            ],
            LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, location_input)
            ],
            DISTRICT: [
                CallbackQueryHandler(district_choice, pattern=r"^district_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, district_input)
            ],
            TIME: [
                CallbackQueryHandler(time_choice, pattern=r"^time_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, time_input)
            ],
            CONFIRMATION: [
                CallbackQueryHandler(confirm_choice, pattern=r"^confirm_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="sport_conversation",
        persistent=False
    )

    application.add_handler(sport_now_conv_handler)

    # Callback query handlers for non-conversation buttons
    application.add_handler(CallbackQueryHandler(handle_clear_chat_callback, pattern=r"^clear_chat_"))

    # Fallback for text messages - only handle text not captured by conversation
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_text))

    logger.info("All handlers have been set up")