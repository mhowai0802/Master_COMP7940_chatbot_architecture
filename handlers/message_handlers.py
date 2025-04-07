import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from services.gpt_router import GPTRouter
from utils.sport_functions import save_sport_now, find_sport_buddies, get_activity_stats

logger = logging.getLogger(__name__)

# Initialize GPT router
gpt_router = GPTRouter()

# Define conversation states for sport registration
NAME, SPORT, LOCATION, DISTRICT, TIME, CONFIRMATION = range(6)

# Common sports list for quick selection
COMMON_SPORTS = ["Basketball", "Football", "Tennis", "Badminton", "Running",
                 "Swimming", "Volleyball", "Table Tennis"]

# Districts in Hong Kong for quick selection
HK_DISTRICTS = [
    "Central and Western",  # Combined for official accuracy
    "Eastern",
    "Islands",
    "Kowloon City",
    "Kwai Tsing",
    "Kwun Tong",
    "North",
    "Sai Kung",
    "Sha Tin",
    "Sham Shui Po",
    "Southern",
    "Tai Po",
    "Tuen Mun",
    "Tsuen Wan",
    "Wan Chai",
    "Wong Tai Sin",
    "Yau Tsim Mong",  # Covers Tsim Sha Tsui, Yau Ma Tei, Mong Kok
    "Yuen Long"
]


# Helper functions to create keyboards
def create_grid_keyboard(items, prefix, buttons_per_row=2, add_other=True):
    """Create a grid keyboard from a list of items."""
    keyboard = []
    row = []

    for i, item in enumerate(items):
        row.append(InlineKeyboardButton(item, callback_data=f"{prefix}_{item}"))
        if (i + 1) % buttons_per_row == 0 or i == len(items) - 1:
            keyboard.append(row.copy())  # Use a copy to avoid reference issues
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
            keyboard.append(row.copy())  # Use a copy to avoid reference issues
            row = []

    keyboard.append([InlineKeyboardButton("Other Time", callback_data="time_other")])
    return InlineKeyboardMarkup(keyboard)


def start(update: Update, context: CallbackContext) -> None:
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

    update.message.reply_text(welcome_message)

    # Follow up with a prompt
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="So, what's your sports plan for today? Ready to play or looking for teammates?"
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    try:
        help_text = (
            "🏆 Sports Buddy Bot Help 🏆\n\n"
            "Available Commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/sport_now - Register that you're playing a sport now\n"
            "/find_sport_buddy - Find people to play sports with\n"
            "/stats - View activity statistics\n\n"
            "You can also just chat with me naturally about your sports plans!"
        )
        logger.info(f"Sending help message to user {update.effective_user.id}")
        update.message.reply_text(help_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in help_command: {str(e)}")
        # Fallback to plain text if Markdown fails
        update.message.reply_text(
            "Sports Buddy Bot Help\n\n"
            "Available Commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/sport_now - Register that you're playing a sport now\n"
            "/find_sport_buddy - Find people to play sports with\n"
            "/stats - View activity statistics\n\n"
            "You can also just chat with me naturally about your sports plans!"
        )


def sport_now_command(update: Update, context: CallbackContext) -> None:
    """Start the sport now registration process"""
    # Get the Telegram username as the default
    user = update.effective_user
    default_name = user.first_name

    # Store the default name in case they just press enter or skip
    context.user_data['default_name'] = default_name
    context.user_data['conversation_state'] = NAME

    update.message.reply_text(
        f"I'll use your Telegram name ({default_name}) by default, but you can provide a different "
        f"name if you prefer. What name would you like to use?"
    )


def find_sport_buddy(update: Update, context: CallbackContext) -> None:
    """Help find sport buddies."""
    results = find_sport_buddies()

    if not results:
        update.message.reply_text(
            "Sorry, I couldn't find anyone playing sports right now. Be the first by using /sport_now!"
        )
        return

    response = "Here are people playing sports today:\n\n"
    for result in results:
        response += (f"- {result['name']} is playing {result['sport']} at {result['datetime']} "
                     f"in {result['location']} ({result['district']})\n\n")

    response += "Send them a message to join!"
    update.message.reply_text(response)


def stats_command(update: Update, context: CallbackContext) -> None:
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

    update.message.reply_text(message, parse_mode='Markdown')


def clear_chat(update: Update, context: CallbackContext) -> None:
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

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Are you sure you want to clear our chat history, {user.first_name}?",
        reply_to_message_id=update.message.message_id,
        reply_markup=reply_markup
    )


def show_confirmation(message, context):
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

    message.reply_text(confirmation_text, reply_markup=reply_markup, parse_mode='Markdown')
    context.user_data['conversation_state'] = CONFIRMATION


def process_name(update: Update, context: CallbackContext) -> None:
    """Process the user's name input"""
    text = update.message.text.strip()

    # If they entered a blank or very short text, use the default name
    if len(text) < 2:
        context.user_data['name'] = context.user_data.get('default_name', update.effective_user.first_name)
        update.message.reply_text(f"Using your default name: {context.user_data['name']}")
    else:
        # Save the user's input name
        context.user_data['name'] = text
        update.message.reply_text(f"Thanks, {text}! Now let's continue.")

    # Check if we already have a sport (from intent detection)
    if 'sport' in context.user_data:
        sport = context.user_data['sport']

        # If we also have a location, ask for district
        if 'location' in context.user_data:
            location = context.user_data['location']
            # Create district selection keyboard
            reply_markup = create_grid_keyboard(HK_DISTRICTS, "district", 3)
            update.message.reply_text(
                f"Great! You'll be playing {sport} at {location}.\n\n"
                f"Which district is this in?",
                reply_markup=reply_markup
            )
            context.user_data['conversation_state'] = DISTRICT
        else:
            # Ask for location
            update.message.reply_text(
                f"Where will you be playing {sport}?\n"
                f"(e.g., Victoria Park Basketball Court, HKBU Sports Centre)"
            )
            context.user_data['conversation_state'] = LOCATION
    else:
        # If we don't have a sport yet, ask for it
        reply_markup = create_grid_keyboard(COMMON_SPORTS, "sport", 2)
        update.message.reply_text(
            "What sport will you be playing?",
            reply_markup=reply_markup
        )
        context.user_data['conversation_state'] = SPORT


def process_sport(update: Update, context: CallbackContext) -> None:
    """Process text input for sport"""
    text = update.message.text.strip()
    context.user_data['sport'] = text
    logger.info(f"Set sport from text: {text}")

    update.message.reply_text(
        f"Great! You'll be playing {text}. What's the specific location?\n"
        f"(e.g., Victoria Park Basketball Court, HKBU Sports Centre)"
    )
    context.user_data['conversation_state'] = LOCATION


def process_location(update: Update, context: CallbackContext) -> None:
    """Process text input for location"""
    text = update.message.text.strip()
    context.user_data['location'] = text
    logger.info(f"Set location: {text}")

    # Create district selection keyboard
    reply_markup = create_grid_keyboard(HK_DISTRICTS, "district", 3)

    update.message.reply_text("Which district is this in?", reply_markup=reply_markup)
    context.user_data['conversation_state'] = DISTRICT


def process_district(update: Update, context: CallbackContext) -> None:
    """Process text input for district"""
    text = update.message.text.strip()
    context.user_data['district'] = text
    logger.info(f"Set district from text: {text}")

    # Create time suggestion keyboard
    current_hour = datetime.now().hour
    reply_markup = create_time_keyboard(current_hour)

    update.message.reply_text("What time will you be playing today?", reply_markup=reply_markup)
    context.user_data['conversation_state'] = TIME


def process_time(update: Update, context: CallbackContext) -> None:
    """Process text input for time"""
    text = update.message.text.strip()
    context.user_data['time'] = text
    logger.info(f"Set time from text: {text}")

    # Call show_confirmation with the message object
    show_confirmation(update.message, context)


def handle_sport_choice(update: Update, context: CallbackContext) -> None:
    """Handle sport selection"""
    query = update.callback_query

    # Ensure we answer the callback to prevent hanging UI
    query.answer()

    # Log the callback
    logger.info(f"Received sport choice callback: {query.data}")

    choice = query.data.replace("sport_", "")

    if choice == "other":
        query.message.edit_text("Please type the name of the sport you'll be playing:")
        context.user_data['conversation_state'] = SPORT
    else:
        context.user_data['sport'] = choice
        logger.info(f"User selected sport: {choice}")

        # Now ask for location
        query.message.edit_text(
            f"Great! You'll be playing {choice}. What's the specific location?\n"
            f"(e.g., Victoria Park Basketball Court, HKBU Sports Centre)"
        )
        context.user_data['conversation_state'] = LOCATION


def handle_district_choice(update: Update, context: CallbackContext) -> None:
    """Handle district selection"""
    query = update.callback_query
    query.answer()

    logger.info(f"Received district choice callback: {query.data}")

    choice = query.data.replace("district_", "")

    if choice == "other":
        query.message.edit_text("Please type the name of the district:")
        context.user_data['conversation_state'] = DISTRICT
    else:
        context.user_data['district'] = choice
        logger.info(f"Set district: {choice}")

        # Create time suggestion keyboard
        current_hour = datetime.now().hour
        reply_markup = create_time_keyboard(current_hour)

        query.message.edit_text("What time will you be playing today?", reply_markup=reply_markup)
        context.user_data['conversation_state'] = TIME


def handle_time_choice(update: Update, context: CallbackContext) -> None:
    """Handle time selection"""
    query = update.callback_query
    query.answer()

    logger.info(f"Received time choice callback: {query.data}")

    choice = query.data.replace("time_", "")

    if choice == "other":
        query.message.edit_text("Please enter the time (e.g., 14:30, 2:30 PM):")
        context.user_data['conversation_state'] = TIME
    else:
        context.user_data['time'] = choice
        logger.info(f"Set time from callback: {choice}")

        # Call show_confirmation directly with the message object
        show_confirmation(query.message, context)


def handle_confirm_choice(update: Update, context: CallbackContext) -> None:
    """Handle confirmation choice"""
    query = update.callback_query
    query.answer()

    logger.info(f"Received confirmation callback: {query.data}")

    choice = query.data.replace("confirm_", "")

    if choice == "yes":
        # Format the data for the database
        user = update.effective_user

        # Use the name that was input/confirmed earlier in the conversation
        name = context.user_data['name']  # This is the name the user provided

        sport_info = {
            'sport': context.user_data['sport'],
            'location': context.user_data['location'],
            'district': context.user_data['district'],
            'datetime': context.user_data['time'],
            'date': datetime.now().strftime("%Y-%m-%d")
        }

        # Save to database using the name from user_data, not user.first_name
        try:
            if save_sport_now(sport_info, name):
                query.message.edit_text(
                    f"✅ Great! Your activity has been registered.\n\n"
                    f"I'll let others know {name} is playing {sport_info['sport']} at "
                    f"{sport_info['datetime']} in {sport_info['location']}.\n\n"
                    f"Have fun playing! 🎉"
                )
            else:
                query.message.edit_text(
                    "Sorry, there was an error saving your information. Please try again."
                )
        except Exception as e:
            logger.error(f"Error saving sport activity: {str(e)}")
            query.message.edit_text(
                "Sorry, there was an error saving your information. Please try again."
            )
    else:
        query.message.edit_text("Registration cancelled. Feel free to try again when you're ready!")

    # Clear user data
    context.user_data.clear()
    logger.info("Conversation ended, user data cleared")


def handle_callback_query(update: Update, context: CallbackContext) -> None:
    """Central handler for callback queries"""
    query = update.callback_query

    logger.info(f"Received callback query: {query.data}")

    try:
        if query.data.startswith("sport_"):
            handle_sport_choice(update, context)
        elif query.data.startswith("district_"):
            handle_district_choice(update, context)
        elif query.data.startswith("time_"):
            handle_time_choice(update, context)
        elif query.data.startswith("confirm_"):
            handle_confirm_choice(update, context)
        elif query.data.startswith("clear_chat_"):
            if query.data == "clear_chat_confirm":
                # Delete the confirmation message
                query.message.delete()

                # Send the cleared message
                cleared_message = (
                    "🧹 Chat cleared! 🧹\n\n"
                    "I've reset our conversation. Let's start fresh!\n\n"
                    "What would you like to do now?\n"
                    "• Use /sport_now to register a sport activity\n"
                    "• Use /find_sport_buddy to find sports partners\n"
                    "• Just chat with me about your sports interests"
                )
                context.bot.send_message(chat_id=query.message.chat_id, text=cleared_message)

                # Clear any user data
                if hasattr(context, 'user_data'):
                    context.user_data.clear()

                logger.info(f"Chat cleared for user {update.effective_user.id}")
            else:
                query.message.edit_text("Chat history will be kept. Continue our conversation!")
        else:
            # Unknown callback data
            logger.warning(f"Unknown callback data: {query.data}")
            query.answer(text="I don't understand this button. Please try a different option.")
    except Exception as e:
        logger.error(f"Error handling callback query: {str(e)}")
        query.answer(text="An error occurred. Please try again.")


def handle_message(update: Update, context: CallbackContext) -> None:
    """Process text messages and determine if they're part of a conversation or new intent"""
    if not update.message:
        # This might be a callback query, not a message
        return

    message = update.message.text
    user = update.effective_user

    logger.info(f"Processing text from {user.first_name} ({user.id}): {message[:50]}...")

    # Check if we're in the middle of a conversation
    if 'conversation_state' in context.user_data:
        current_state = context.user_data['conversation_state']
        logger.info(f"Continuing conversation at state: {current_state}")

        # Process based on the current state
        if current_state == NAME:
            process_name(update, context)
        elif current_state == SPORT:
            process_sport(update, context)
        elif current_state == LOCATION:
            process_location(update, context)
        elif current_state == DISTRICT:
            process_district(update, context)
        elif current_state == TIME:
            process_time(update, context)
        return

    # If not in a conversation, process as a new message with intent detection
    try:
        # Get intent from GPT router
        intent_data = gpt_router.route_intent(message)
        intent = intent_data.get('intent', 'general_question')
        extracted = intent_data.get('extracted_data', {})

        logger.info(f"Intent classified as: {intent}")

        # Handle based on intent
        if intent == 'sport_now':
            # Start sport registration flow

            # Store default name
            context.user_data['default_name'] = user.first_name

            # Store sport if available
            sport_detected = extracted.get('sport')
            if not sport_detected:
                for sport in COMMON_SPORTS:
                    if sport.lower() in message.lower():
                        sport_detected = sport
                        break

            if sport_detected:
                context.user_data['sport'] = sport_detected

            # Store location if available
            if 'location' in extracted and extracted['location']:
                context.user_data['location'] = extracted['location']

            # Store time if available
            if 'time' in extracted and extracted['time']:
                context.user_data['time'] = extracted['time']

            # Ask for name first
            update.message.reply_text(
                f"I see you want to play sports! What name would you like to use?\n"
                f"I'll use your Telegram name ({user.first_name}) by default, "
                f"but you can provide a different name if you prefer."
            )

            context.user_data['conversation_state'] = NAME

        elif intent == 'find_buddy':
            # They want to find sport buddies
            find_sport_buddy(update, context)

        else:
            # General question about sports
            response = gpt_router.get_sport_response(message)
            update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        update.message.reply_text(
            "Sorry, I'm having a bit of trouble right now. Please try again or use one of my commands like /sport_now or /find_sport_buddy."
        )