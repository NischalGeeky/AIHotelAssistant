from typing import Dict, Any, List, Optional
from services.hotel_service import HotelService
from services.booking_service import BookingService
from utils.parser import parse_booking_request

# Initialize services
hotel_service = HotelService()
booking_service = BookingService()

def search_hotels_tool(location: str, budget: Optional[int] = None, guests: int = 1, 
                       preferences: List[str] = None, nights: int = 1) -> Dict[str, Any]:
    """
    Tool for searching hotels based on criteria
    
    Args:
        location: City/destination
        budget: Maximum budget per night
        guests: Number of guests
        preferences: List of preferred amenities
        nights: Number of nights
    
    Returns:
        Dictionary with search results and metadata
    """
    search_criteria = {
        'location': location,
        'budget': budget,
        'guests': guests,
        'preferences': preferences or [],
        'nights': nights
    }
    
    hotels = hotel_service.search_hotels(search_criteria)
    
    return {
        'success': True,
        'hotels': hotels,
        'count': len(hotels),
        'criteria': search_criteria
    }

def extract_preferences_tool(user_input: str) -> Dict[str, Any]:
    """
    Tool for extracting user preferences from natural language
    
    Args:
        user_input: Natural language input from user
    
    Returns:
        Structured preferences dictionary
    """
    from models.llm import extract_user_preferences
    
    try:
        preferences = extract_user_preferences(user_input)
        return {
            'success': True,
            'preferences': preferences
        }
    except Exception as e:
        # Fallback to basic parsing
        basic_prefs = parse_booking_request(user_input)
        return {
            'success': True,
            'preferences': basic_prefs
        }

def book_hotel_tool(hotel_id: int, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool for booking a hotel
    
    Args:
        hotel_id: ID of the hotel to book
        user_preferences: User booking details
    
    Returns:
        Booking confirmation or error
    """
    hotel = hotel_service.get_hotel_by_id(hotel_id)
    if not hotel:
        return {
            'success': False,
            'error': 'Hotel not found'
        }
    
    try:
        booking = booking_service.create_booking(hotel, user_preferences)
        return {
            'success': True,
            'booking': booking
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_hotel_details_tool(hotel_id: int) -> Dict[str, Any]:
    """
    Tool for getting detailed hotel information
    
    Args:
        hotel_id: ID of the hotel
    
    Returns:
        Hotel details or error
    """
    hotel = hotel_service.get_hotel_by_id(hotel_id)
    if hotel:
        return {
            'success': True,
            'hotel': hotel
        }
    else:
        return {
            'success': False,
            'error': 'Hotel not found'
        }

def get_booking_details_tool(booking_id: str) -> Dict[str, Any]:
    """
    Tool for getting booking details
    
    Args:
        booking_id: Booking ID
    
    Returns:
        Booking details or error
    """
    booking = booking_service.get_booking_by_id(booking_id)
    if booking:
        return {
            'success': True,
            'booking': booking
        }
    else:
        return {
            'success': False,
            'error': 'Booking not found'
        }

def cancel_booking_tool(booking_id: str) -> Dict[str, Any]:
    """
    Tool for cancelling a booking
    
    Args:
        booking_id: Booking ID to cancel
    
    Returns:
        Cancellation result
    """
    success = booking_service.cancel_booking(booking_id)
    return {
        'success': success,
        'message': 'Booking cancelled successfully' if success else 'Failed to cancel booking'
    }

def get_popular_destinations_tool() -> Dict[str, Any]:
    """
    Tool for getting popular destinations
    
    Returns:
        List of popular destinations with hotel counts
    """
    destinations = hotel_service.get_popular_destinations()
    return {
        'success': True,
        'destinations': destinations
    }

def calculate_cost_tool(hotel_id: int, nights: int) -> Dict[str, Any]:
    """
    Tool for calculating total stay cost
    
    Args:
        hotel_id: Hotel ID
        nights: Number of nights
    
    Returns:
        Cost calculation
    """
    hotel = hotel_service.get_hotel_by_id(hotel_id)
    if not hotel:
        return {
            'success': False,
            'error': 'Hotel not found'
        }
    
    total_cost = hotel_service.calculate_total_cost(hotel, nights)
    return {
        'success': True,
        'hotel_name': hotel['name'],
        'price_per_night': hotel['price_per_night'],
        'nights': nights,
        'total_cost': total_cost
    }

# Tool definitions for LLM
AVAILABLE_TOOLS = {
    'search_hotels': {
        'name': 'search_hotels',
        'description': 'Search for hotels based on location, budget, guests, and preferences',
        'parameters': {
            'location': {'type': 'string', 'description': 'City or destination'},
            'budget': {'type': 'integer', 'description': 'Maximum budget per night (optional)'},
            'guests': {'type': 'integer', 'description': 'Number of guests (default: 1)'},
            'preferences': {'type': 'array', 'description': 'List of preferred amenities (optional)'},
            'nights': {'type': 'integer', 'description': 'Number of nights (default: 1)'}
        }
    },
    'extract_preferences': {
        'name': 'extract_preferences',
        'description': 'Extract structured preferences from user natural language input',
        'parameters': {
            'user_input': {'type': 'string', 'description': 'Natural language input from user'}
        }
    },
    'book_hotel': {
        'name': 'book_hotel',
        'description': 'Book a hotel with given preferences',
        'parameters': {
            'hotel_id': {'type': 'integer', 'description': 'ID of the hotel to book'},
            'user_preferences': {'type': 'object', 'description': 'User booking details'}
        }
    },
    'get_hotel_details': {
        'name': 'get_hotel_details',
        'description': 'Get detailed information about a specific hotel',
        'parameters': {
            'hotel_id': {'type': 'integer', 'description': 'ID of the hotel'}
        }
    },
    'get_booking_details': {
        'name': 'get_booking_details',
        'description': 'Get details of a specific booking',
        'parameters': {
            'booking_id': {'type': 'string', 'description': 'Booking ID'}
        }
    },
    'cancel_booking': {
        'name': 'cancel_booking',
        'description': 'Cancel a booking',
        'parameters': {
            'booking_id': {'type': 'string', 'description': 'Booking ID to cancel'}
        }
    },
    'get_popular_destinations': {
        'name': 'get_popular_destinations',
        'description': 'Get popular destinations with hotel counts and average prices',
        'parameters': {}
    },
    'calculate_cost': {
        'name': 'calculate_cost',
        'description': 'Calculate total cost for a hotel stay',
        'parameters': {
            'hotel_id': {'type': 'integer', 'description': 'Hotel ID'},
            'nights': {'type': 'integer', 'description': 'Number of nights'}
        }
    }
}

def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool by name with given parameters
    
    Args:
        tool_name: Name of the tool to execute
        parameters: Parameters for the tool
    
    Returns:
        Tool execution result
    """
    tool_functions = {
        'search_hotels': search_hotels_tool,
        'extract_preferences': extract_preferences_tool,
        'book_hotel': book_hotel_tool,
        'get_hotel_details': get_hotel_details_tool,
        'get_booking_details': get_booking_details_tool,
        'cancel_booking': cancel_booking_tool,
        'get_popular_destinations': get_popular_destinations_tool,
        'calculate_cost': calculate_cost_tool
    }
    
    if tool_name not in tool_functions:
        return {
            'success': False,
            'error': f'Tool {tool_name} not found'
        }
    
    try:
        return tool_functions[tool_name](**parameters)
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def format_tools_for_llm() -> str:
    """Format available tools for LLM prompt"""
    tools_description = "Available tools:\n\n"
    
    for tool_name, tool_info in AVAILABLE_TOOLS.items():
        tools_description += f"**{tool_name}**: {tool_info['description']}\n"
        tools_description += "Parameters:\n"
        for param_name, param_info in tool_info['parameters'].items():
            tools_description += f"  - {param_name} ({param_info['type']}): {param_info['description']}\n"
        tools_description += "\n"
    
    return tools_description
