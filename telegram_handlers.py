from telegram import Update
from telegram.ext import ContextTypes
from config import logger
from gpt_router import determine_intent, extract_sport_now_info, extract_find_buddy_info, general_response
from sport_functions import save_sport_now, find_sport_buddies


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm your Sports Buddy Bot. I can help you find sports activities and buddies. Use /help to see available commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
    Here are the commands you can use:

    /start - Start the bot
    /help - Show this help message
    /sport_now - Register what sport you're playing now
    /find_sport_buddy - Find someone to play sports with

    You can also just chat with me normally, and I'll understand what you need help with!
    """
    await update.message.reply_text(help_text)


async def sport_now_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /sport_now command."""
    await update.message.reply_text(
        "Please tell me what sport you're playing, when, and where. For example: 'I'm playing basketball tonight at 7pm in Central Park, Hong Kong Island'")
    context.user_data["expecting_sport_now"] = True


async def find_sport_buddy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /find_sport_buddy command."""
    await update.message.reply_text("What sport are you looking to play and where are you located?")
    context.user_data["expecting_find_buddy"] = True


async def process_sport_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process sport now information."""
    user_message = update.message.text
    user = update.effective_user

    # Extract sport details
    sport_info = extract_sport_now_info(user_message)

    # Check if we got all the required information
    if not all(k in sport_info for k in ['sport', 'datetime', 'location']):
        await update.message.reply_text(
            "I couldn't understand all the details. Please provide the sport, time, and location clearly.")
        return

    # Save to database
    if save_sport_now(sport_info, user.first_name):
        await update.message.reply_text(
            f"Great! I've registered that you're playing {sport_info['sport']} at {sport_info['datetime']} in {sport_info['location']}. Have fun!")
    else:
        await update.message.reply_text("Sorry, there was an error saving your information. Please try again.")


async def process_find_buddy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process find buddy request."""
    user_message = update.message.text

    # Extract search criteria
    search_info = extract_find_buddy_info(user_message)

    # Check if we got the required information
    if 'sport' not in search_info or not search_info['sport']:
        await update.message.reply_text(
            "I couldn't understand what sport you're looking for. Please specify the sport clearly.")
        return

    # Find matches
    sport_query = search_info.get('sport', '')
    district_query = search_info.get('district', '')

    matches, location_counts = find_sport_buddies(sport_query, district_query)

    if not matches:
        await update.message.reply_text(
            f"I couldn't find anyone playing {sport_query} right now. Try registering yourself with /sport_now so others can find you!")
        return

    # Format response
    response = f"Here are people playing {sport_query}:\n\n"
    for match in matches:
        response += f"• {match.get('name', 'Someone')} is playing {match.get('sport')} at {match.get('datetime')} in {match.get('location')}, {match.get('district')}\n"

    response += "\nPlayer count by location:\n"
    for location, count in location_counts.items():
        response += f"• {location}: {count} player(s)\n"

    await update.message.reply_text(response)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages with GPT routing."""
    user_message = update.message.text

    # Check if we're in a specific flow
    if context.user_data.get("expecting_sport_now"):
        await process_sport_now(update, context)
        context.user_data["expecting_sport_now"] = False
        return

    if context.user_data.get("expecting_find_buddy"):
        await process_find_buddy(update, context)
        context.user_data["expecting_find_buddy"] = False
        return

    # Use GPT to determine intent
    intent = determine_intent(user_message)

    if "sport_now" in intent:
        context.user_data["expecting_sport_now"] = True
        await update.message.reply_text(
            "I'll help you register your current sport activity. Please tell me what sport you're playing, when, and where.")
    elif "find_sport_buddy" in intent:
        context.user_data["expecting_find_buddy"] = True
        await update.message.reply_text(
            "I'll help you find a sports buddy. What sport are you looking to play and where are you located?")
    else:
        # General conversation
        response = general_response(user_message)
        await update.message.reply_text(response)