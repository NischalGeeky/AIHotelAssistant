import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

def parse_booking_request(user_input: str) -> Dict[str, Any]:
    """
    Parse user booking request and extract structured information.
    This is a fallback parser when LLM extraction fails.
    """
    user_input_lower = user_input.lower()
    
    # Initialize result
    result = {
        "location": None,
        "check_in": None,
        "check_out": None,
        "guests": 1,
        "budget": None,
        "preferences": [],
        "nights": None,
        "intent": "search"  # Default intent
    }
    
    # Extract intent
    result["intent"] = extract_intent(user_input_lower)
    
    # Extract location
    result["location"] = extract_location(user_input_lower)
    
    # Extract dates
    dates = extract_dates(user_input_lower)
    result.update(dates)
    
    # Extract number of guests
    result["guests"] = extract_guests(user_input_lower)
    
    # Extract budget
    result["budget"] = extract_budget(user_input_lower)
    
    # Extract preferences/amenities
    result["preferences"] = extract_preferences(user_input_lower)
    
    # Calculate nights if check-in and check-out are provided
    if result["check_in"] and result["check_out"]:
        result["nights"] = calculate_nights(result["check_in"], result["check_out"])
    
    return result

def extract_intent(user_input: str) -> str:
    """Extract user intent from the input"""
    search_keywords = ["find", "search", "looking for", "need", "want", "show me", "get me"]
    book_keywords = ["book", "reserve", "confirm", "booking"]
    refine_keywords = ["filter", "only", "with", "prefer", "must have", "should have"]
    
    if any(keyword in user_input for keyword in book_keywords):
        return "booking"
    elif any(keyword in user_input for keyword in refine_keywords):
        return "refinement"
    elif any(keyword in user_input for keyword in search_keywords):
        return "search"
    else:
        return "search"  # Default to search

def extract_location(user_input: str) -> Optional[str]:
    """Extract location from user input"""
    locations = [
        "bangalore", "bengaluru", "mumbai", "delhi", "new delhi", "goa", 
        "kerala", "manali", "pune", "hyderabad", "chennai", "jaipur",
        "kolkata", "ahmedabad", "surat", "lucknow", "kanpur", "nagpur"
    ]
    
    for location in locations:
        if location in user_input:
            return location.title()
    
    return None

def extract_dates(user_input: str) -> Dict[str, Any]:
    """Extract check-in and check-out dates"""
    result = {"check_in": None, "check_out": None, "nights": None}
    
    # Pattern for "X nights" or "for X days"
    nights_pattern = r'(\d+)\s*(nights?|days?)'
    nights_match = re.search(nights_pattern, user_input)
    if nights_match:
        result["nights"] = int(nights_match.group(1))
    
    # Pattern for specific dates (simplified - would need more sophisticated date parsing)
    # This is a basic implementation - in production, you'd want more robust date parsing
    date_patterns = [
        r'today', r'tomorrow', r'next week', r'next month',
        r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',  # DD/MM/YYYY
        r'(\d{1,2})[/\-](\d{1,2})',  # DD/MM (assuming current year)
    ]
    
    # For now, we'll keep it simple and not parse specific dates
    # In a real implementation, you'd use a library like dateparser
    
    return result

def extract_guests(user_input: str) -> int:
    """Extract number of guests"""
    guests_pattern = r'(\d+)\s*(guests?|people|person)'
    match = re.search(guests_pattern, user_input)
    
    if match:
        return int(match.group(1))
    
    # Check for "for me", "for us", etc.
    if "for us" in user_input:
        # Could be 2 or more, but we'll default to 2
        return 2
    elif "for me" in user_input or "myself" in user_input:
        return 1
    
    return 1  # Default to 1 guest

def extract_budget(user_input: str) -> Optional[int]:
    """Extract budget from user input"""
    budget_patterns = [
        r'under\s*(\d+)',
        r'below\s*(\d+)',
        r'less than\s*(\d+)',
        r'maximum\s*(\d+)',
        r'budget\s*(\d+)',
        r'(\d+)\s*rupees?',
        r'(\d+)\s*rs?',
        r'₹(\d+)',
        r'(\d+)\s*budget'
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, user_input)
        if match:
            return int(match.group(1))
    
    return None

def extract_preferences(user_input: str) -> List[str]:
    """Extract hotel preferences/amenities"""
    preference_keywords = {
        "wifi": ["wifi", "internet", "wi-fi", "web", "online"],
        "pool": ["pool", "swimming", "swim", "swimming pool"],
        "breakfast": ["breakfast", "food", "meal", "dining"],
        "ac": ["ac", "air conditioning", "aircon", "air condition"],
        "parking": ["parking", "car", "vehicle", "park"],
        "gym": ["gym", "fitness", "workout", "exercise"],
        "spa": ["spa", "massage", "wellness", "relaxation"],
        "restaurant": ["restaurant", "dining", "food", "cuisine"],
        "beach_access": ["beach", "beachfront", "sea", "ocean"],
        "mountain_view": ["mountain", "hill", "view", "scenic"],
        "business_center": ["business", "work", "office", "meeting"]
    }
    
    found_preferences = []
    
    for preference, keywords in preference_keywords.items():
        if any(keyword in user_input for keyword in keywords):
            found_preferences.append(preference)
    
    return found_preferences

def calculate_nights(check_in: str, check_out: str) -> Optional[int]:
    """Calculate number of nights between check-in and check-out"""
    try:
        # This is a simplified implementation
        # In production, you'd use proper date parsing
        if check_in and check_out:
            # For now, return None as we don't have proper date parsing
            return None
    except:
        pass
    
    return None

def parse_booking_confirmation(user_input: str) -> Dict[str, Any]:
    """Parse booking confirmation details"""
    result = {
        "confirmed": False,
        "hotel_index": None,
        "guest_name": None,
        "contact": None,
        "special_requests": []
    }
    
    user_input_lower = user_input.lower()
    
    # Check for confirmation
    if any(word in user_input_lower for word in ["yes", "confirm", "book", "proceed", "ok"]):
        result["confirmed"] = True
    
    # Extract hotel selection
    hotel_patterns = [
        r'first one', r'second one', r'third one', r'fourth one', r'fifth one',
        r'hotel (\d+)', r'option (\d+)', r'number (\d+)'
    ]
    
    for pattern in hotel_patterns:
        match = re.search(pattern, user_input_lower)
        if match:
            if "first" in pattern:
                result["hotel_index"] = 0
            elif "second" in pattern:
                result["hotel_index"] = 1
            elif "third" in pattern:
                result["hotel_index"] = 2
            elif "fourth" in pattern:
                result["hotel_index"] = 3
            elif "fifth" in pattern:
                result["hotel_index"] = 4
            else:
                result["hotel_index"] = int(match.group(1)) - 1
            break
    
    return result

def is_complete_booking_request(preferences: Dict[str, Any]) -> bool:
    """Check if the booking request has enough information to proceed"""
    required_fields = ["location"]
    
    for field in required_fields:
        if not preferences.get(field):
            return False
    
    return True

def get_missing_information(preferences: Dict[str, Any]) -> List[str]:
    """Get list of missing information needed for booking"""
    missing = []
    
    if not preferences.get("location"):
        missing.append("location")
    
    if not preferences.get("guests"):
        missing.append("number of guests")
    
    # Optional but helpful
    if not preferences.get("budget"):
        missing.append("budget (optional)")
    
    return missing

def format_preferences_for_display(preferences: Dict[str, Any]) -> str:
    """Format preferences for user confirmation"""
    parts = []
    
    if preferences.get("location"):
        parts.append(f"Location: {preferences['location']}")
    
    if preferences.get("guests"):
        parts.append(f"Guests: {preferences['guests']}")
    
    if preferences.get("budget"):
        parts.append(f"Budget: ₹{preferences['budget']}")
    
    if preferences.get("nights"):
        parts.append(f"Nights: {preferences['nights']}")
    
    if preferences.get("preferences"):
        parts.append(f"Preferences: {', '.join(preferences['preferences'])}")
    
    return " | ".join(parts) if parts else "No specific preferences"
