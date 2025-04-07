import logging
import json

from services.chatgpt_service import HKBU_ChatGPT

logger = logging.getLogger(__name__)

class GPTRouter:
    def __init__(self):
        self.chatgpt = HKBU_ChatGPT()
        logger.info("GPTRouter initialized")

    def route_intent(self, message):
        """
        Determine the user's intent from their message
        """
        prompt = (
            "You are an intent classifier for a sports buddy telegram bot. "
            "Your task is to identify what the user wants based on their message. "
            "Here are the possible intents:\n"
            "1. sport_now - User are playing a sport now\n"
            "2. find_buddy - User wants to find people to play sports with\n"
            "3. general_question - User has a general question about sports\n"
            "If the intent is sport_now, also try to extract:\n"
            "- sport: What sport they're playing\n"
            "- location: Where they're playing\n"
            "- time: When they're playing\n\n"
            "Return your answer as a JSON dictionary with this format with no additional text:\n"
            "{'intent': 'intent_name', 'extracted_data': {'key': 'value'}}\n\n"
            f"User message: {message}"
        )

        logger.info(f"Routing intent for message: {message[:50]}...")

        try:
            # Get response from the model
            response = self.chatgpt.submit(prompt)

            # Clean up the response
            response = response.strip()
            if response.find('{') >= 0 and response.rfind('}') >= 0:
                start = response.find('{')
                end = response.rfind('}') + 1
                response = response[start:end]

            # Use json instead of eval for safer parsing
            try:
                intent_data = json.loads(response.replace("'", "\""))
                logger.info(f"Intent classified as: {intent_data.get('intent', 'unknown')}")
                return intent_data
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse intent from response: {e}, using fallback")

                # Simple keyword-based fallback
                if 'sport_now' in response.lower():
                    return {"intent": "sport_now", "extracted_data": {}}
                elif 'find_buddy' in response.lower():
                    return {"intent": "find_buddy", "extracted_data": {}}
                else:
                    return {"intent": "general_question", "extracted_data": {}}

        except Exception as e:
            logger.error(f"Error in GPT routing: {str(e)}")
            return {
                "intent": "general_question",
                "extracted_data": {}
            }

    def get_sport_response(self, user_query, context=None):
        """
        Get a sports-focused response to a user query
        """
        prompt = (
            "You are a helpful sports assistant for a sports buddy telegram bot. "
            "Give concise, sports-focused answers. Be friendly but direct. "
            "If someone asks about sports activities, fitness, training, "
            "or finding sports buddies, provide practical advice.\n\n"
        )

        if context:
            prompt += f"Context: {context}\n\n"

        prompt += f"User query: {user_query}"

        try:
            response = self.chatgpt.submit(prompt)
            return response
        except Exception as e:
            logger.error(f"Error getting sport response: {str(e)}")
            return "Sorry, I'm having trouble answering that right now. Please try again later."