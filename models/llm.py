import os
import json
import re
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# Initialize Groq LLM
def get_llm_client():
    """Initialize and return Groq LLM client"""
    api_key = os.getenv("GROQ_API_KEY", "gsk_your_api_key_here")  # Replace with actual API key
    return ChatGroq(
        groq_api_key=api_key,
        model_name="llama3-70b-8192",
        temperature=0.1
    )

def get_llm_response(messages: list, system_prompt: Optional[str] = None) -> str:
    """Get response from LLM"""
    try:
        llm = get_llm_client()
        
        # Add system message if provided
        if system_prompt:
            formatted_messages = [SystemMessage(content=system_prompt)] + messages
        else:
            formatted_messages = messages
        
        response = llm.invoke(formatted_messages)
        return response.content
    
    except Exception as e:
        return f"Error getting LLM response: {str(e)}"

def extract_user_preferences(user_input: str) -> Dict[str, Any]:
    """Extract structured preferences from user input using LLM"""
    
    template = """
    You are a hotel booking assistant. Extract the following information from the user's request and return it as JSON:
    
    {
        "location": "city name or null",
        "check_in": "YYYY-MM-DD or null", 
        "check_out": "YYYY-MM-DD or null",
        "guests": "number or 1",
        "budget": "number or null",
        "preferences": ["list", "of", "amenities"],
        "nights": "number or null"
    }
    
    User input: {user_input}
    
    Extract only the information that is explicitly mentioned or can be reasonably inferred. If something is not mentioned, use null.
    Return ONLY the JSON object, no other text.
    """
    
    try:
        llm = get_llm_client()
        
        formatted_prompt = template.format(user_input=user_input)
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        
        # Parse the JSON response
        try:
            parsed_response = json.loads(response.content.strip())
            
            # Clean and validate the response
            cleaned_response = {
                "location": parsed_response.get("location"),
                "check_in": parsed_response.get("check_in"),
                "check_out": parsed_response.get("check_out"),
                "guests": int(parsed_response.get("guests", 1)),
                "budget": int(parsed_response.get("budget")) if parsed_response.get("budget") else None,
                "preferences": parsed_response.get("preferences", []),
                "nights": int(parsed_response.get("nights")) if parsed_response.get("nights") else None
            }
            
            return cleaned_response
        except json.JSONDecodeError:
            # Fallback to basic extraction
            return basic_preference_extraction(user_input)
    
    except Exception as e:
        # Fallback to basic extraction if LLM fails
        return basic_preference_extraction(user_input)

def basic_preference_extraction(user_input: str) -> Dict[str, Any]:
    """Fallback basic extraction using keyword matching"""
    user_input_lower = user_input.lower()
    
    # Basic keyword extraction
    locations = ["bangalore", "bengaluru", "mumbai", "delhi", "new delhi", "goa", 
                "kerala", "manali", "pune", "hyderabad", "chennai", "jaipur"]
    location = next((loc for loc in locations if loc in user_input_lower), None)
    
    # Budget extraction
    budget = None
    budget_match = re.search(r'under\s*(\d+)|below\s*(\d+)|(\d+)\s*rupees?|(\d+)\s*rs?|₹(\d+)', user_input_lower)
    if budget_match:
        budget = int(next(filter(None, budget_match.groups())))
    
    # Guests extraction
    guests = 1
    guest_match = re.search(r'(\d+)\s*(guests?|people|person)', user_input_lower)
    if guest_match:
        guests = int(next(filter(None, guest_match.groups())))
    
    # Nights extraction
    nights = None
    nights_match = re.search(r'(\d+)\s*(nights?|days?)', user_input_lower)
    if nights_match:
        nights = int(nights_match.group(1))
    
    # Preferences extraction
    preferences = []
    preference_keywords = {
        "wifi": ["wifi", "internet", "wi-fi"],
        "pool": ["pool", "swimming"],
        "breakfast": ["breakfast", "food"],
        "ac": ["ac", "air conditioning"],
        "parking": ["parking", "car"],
        "gym": ["gym", "fitness"],
        "spa": ["spa", "massage"]
    }
    
    for pref, keywords in preference_keywords.items():
        if any(keyword in user_input_lower for keyword in keywords):
            preferences.append(pref)
    
    return {
        "location": location,
        "check_in": None,
        "check_out": None,
        "guests": guests,
        "budget": budget,
        "preferences": preferences,
        "nights": nights
    }

def generate_hotel_recommendations(hotels: list, preferences: Dict[str, Any]) -> str:
    """Generate natural language recommendations for hotels"""
    
    template = """
    Based on the user's preferences, recommend the best hotels from the available options. Your response should be conversational and friendly.

    User Preferences:
    - Location: {location}
    - Budget: {budget}
    - Guests: {guests}
    - Preferences: {preferences}

    Available Hotels:
    {hotels}

    Provide a friendly, conversational recommendation highlighting the top 3-5 options that best match the user's needs.
    Mention key features, prices, and why each hotel is a good choice.
    """
    
    hotels_str = "\n".join([
        f"{i+1}. {hotel['name']} - {hotel['location']}, ₹{hotel['price_per_night']}/night, ⭐{hotel['rating']}, Amenities: {', '.join(hotel['amenities'])}"
        for i, hotel in enumerate(hotels)
    ])
    
    try:
        llm = get_llm_client()
        
        formatted_prompt = template.format(
            location=preferences.get('location', 'Any'),
            budget=preferences.get('budget', 'No limit'),
            guests=preferences.get('guests', 1),
            preferences=', '.join(preferences.get('preferences', [])),
            hotels=hotels_str
        )
        
        response = llm.invoke([HumanMessage(content=formatted_prompt)])
        return response.content
    
    except Exception as e:
        return f"I found some great options for you: {hotels_str}"

def chat_with_context(user_input: str, conversation_history: list, system_prompt: str) -> str:
    """Chat with conversation context"""
    
    messages = []
    
    # Add system message
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    
    # Add conversation history
    for msg in conversation_history[-5:]:  # Last 5 messages for context
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(SystemMessage(content=msg["content"]))
    
    # Add current user input
    messages.append(HumanMessage(content=user_input))
    
    return get_llm_response(messages)
