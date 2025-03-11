from config import chatgpt, logger


def determine_intent(user_message):
    """Use GPT to determine user intent from natural language."""
    gpt_prompt = f"""As a router for a sports buddy app, determine which function should handle this message: '{user_message}'

    Available functions:
    1. sport_now - For registering what sport the user is playing, when, and where
    2. find_sport_buddy - For finding people to play sports with
    3. general_chat - For general conversation

    Return ONLY THE FUNCTION NAME without explanation."""

    intent = chatgpt.submit(gpt_prompt).strip().lower()
    return intent


def extract_sport_now_info(user_message):
    """Extract sport activity information using GPT."""
    gpt_prompt = f"""Extract the following information from this text: '{user_message}'
    - Sport name
    - Date and time
    - Location
    - District (if mentioned)

    Return the information in JSON format with these exact keys: sport, datetime, location, district"""

    response = chatgpt.submit(gpt_prompt)

    # Try to parse the GPT response as JSON-like structure
    try:
        # Extract key-value pairs from the GPT response
        sport_info = {}
        for line in response.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().strip('"')
                value = value.strip().strip(',').strip('"')
                if key in ['sport', 'datetime', 'location', 'district']:
                    sport_info[key] = value
    except Exception as e:
        logger.error(f"Error parsing GPT response: {e}")
        sport_info = {}

    return sport_info


def extract_find_buddy_info(user_message):
    """Extract sport and location search criteria using GPT."""
    gpt_prompt = f"""Extract the sport and location/district from this text: '{user_message}'
    Return the information in JSON format with these exact keys: sport, district"""

    response = chatgpt.submit(gpt_prompt)

    # Try to parse the GPT response
    try:
        # Extract key-value pairs from the GPT response
        search_info = {}
        for line in response.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().strip('"')
                value = value.strip().strip(',').strip('"')
                if key in ['sport', 'district']:
                    search_info[key] = value
    except Exception as e:
        logger.error(f"Error parsing GPT response: {e}")
        search_info = {}

    return search_info


def general_response(user_message):
    """Generate a general response using GPT."""
    gpt_prompt = f"""You are a friendly sports buddy assistant. The user says: '{user_message}'. 
    Respond helpfully and suggest using commands like /sport_now or /find_sport_buddy if relevant."""

    return chatgpt.submit(gpt_prompt)