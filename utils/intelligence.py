import logging
from typing import Dict, List, Any, Optional, Tuple
from utils.memory import ConversationMemory, ConversationIntent
from services.hotel_service import HotelService
from models.llm import get_llm_client
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class ConversationIntelligence:
    """Advanced conversation intelligence layer"""
    
    def __init__(self, hotel_service: HotelService):
        self.memory = ConversationMemory()
        self.hotel_service = hotel_service
        self.llm = get_llm_client()
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input with intelligent reasoning"""
        logger.info(f"Processing user input: {user_input[:50]}...")
        
        # Detect intent
        intent = self.memory.detect_intent(user_input)
        logger.info(f"Detected intent: {intent.value}")
        
        # Process based on intent
        if intent == ConversationIntent.SEARCH:
            return self._handle_search_intent(user_input)
        elif intent == ConversationIntent.REFINE:
            return self._handle_refine_intent(user_input)
        elif intent == ConversationIntent.BOOK:
            return self._handle_book_intent(user_input)
        elif intent == ConversationIntent.CONFIRMATION:
            return self._handle_confirmation_intent(user_input)
        elif intent == ConversationIntent.HELP:
            return self._handle_help_intent(user_input)
        else:
            return self._handle_unknown_intent(user_input)
    
    def _handle_search_intent(self, user_input: str) -> Dict[str, Any]:
        """Handle search intent with intelligent filtering"""
        from models.llm import extract_user_preferences
        
        # Extract preferences
        preferences = extract_user_preferences(user_input)
        logger.info(f"Extracted preferences: {preferences}")
        
        # Check if follow-up is needed based on extracted preferences
        if not preferences.get("location"):
            return {
                "intent": ConversationIntent.SEARCH,
                "response_type": "follow_up",
                "response": "Which city or location are you looking for?",
                "needs_action": False
            }
        
        # Validate and normalize
        normalized_preferences = self._validate_and_normalize(preferences)
        
        # Update memory
        self.memory.update_state(user_input, "", normalized_preferences)
        
        # Search hotels
        hotels = self.hotel_service.search_hotels_hybrid(normalized_preferences)
        
        if not hotels:
            return self._handle_no_results(normalized_preferences)
        
        # Update memory with results
        self.memory.state.last_results = hotels
        
        # Generate intelligent response
        response = self._generate_search_response(hotels, normalized_preferences)
        
        return {
            "intent": ConversationIntent.SEARCH,
            "response_type": "search_results",
            "response": response,
            "hotels": hotels,
            "needs_action": True
        }
    
    def _handle_refine_intent(self, user_input: str) -> Dict[str, Any]:
        """Handle refinement intent with multi-turn reasoning"""
        refinements = self.memory.detect_refinement_intent(user_input)
        logger.info(f"Detected refinements: {refinements}")
        
        if not refinements:
            # Try to understand what user wants to refine
            response = self._ask_for_clarification()
            return {
                "intent": ConversationIntent.REFINE,
                "response_type": "clarification",
                "response": response,
                "needs_action": False
            }
        
        # Update filters with refinements
        updated_filters = self.memory.state.filters.copy()
        updated_filters.update(refinements)
        
        # Search with updated filters
        hotels = self.hotel_service.search_hotels_hybrid(updated_filters)
        
        if not hotels:
            return self._handle_no_results(updated_filters)
        
        # Update memory
        self.memory.update_state(user_input, "", refinements)
        self.memory.state.last_results = hotels
        
        # Generate refinement response
        response = self._generate_refinement_response(hotels, refinements)
        
        return {
            "intent": ConversationIntent.REFINE,
            "response_type": "refined_results",
            "response": response,
            "hotels": hotels,
            "needs_action": True
        }
    
    def _handle_book_intent(self, user_input: str) -> Dict[str, Any]:
        """Handle booking intent with validation"""
        # Check if hotel is selected via UI (session state)
        selected_hotel = None
        if hasattr(self.memory.state, 'selected_hotel') and self.memory.state.selected_hotel:
            selected_hotel = self.memory.state.selected_hotel
        else:
            # Try to extract hotel selection from user input
            selected_hotel = self._extract_hotel_selection(user_input)
        
        if not selected_hotel:
            response = "Which hotel would you like to book? Please select a hotel from the list or specify by name."
            return {
                "intent": ConversationIntent.BOOK,
                "response_type": "clarification",
                "response": response,
                "needs_action": False
            }
        
        # Validate booking requirements
        missing_fields = self.memory.identify_missing_fields(ConversationIntent.BOOK)
        if missing_fields:
            response = self.memory.generate_follow_up_questions(user_input)
            return {
                "intent": ConversationIntent.BOOK,
                "response_type": "follow_up",
                "response": response,
                "needs_action": False
            }
        
        # Process booking
        try:
            # Use booking service directly
            from services.booking_service import BookingService
            booking_service = BookingService()
            
            booking_preferences = self.memory.state.filters.copy()
            booking_preferences.update({
                'hotel_id': selected_hotel.get('id'),
                'nights': self.memory.state.filters.get('nights', 1),
                'guests': self.memory.state.filters.get('guests', 1)
            })
            
            booking = booking_service.create_booking(selected_hotel, booking_preferences)
            
            if booking:
                response = f"🎉 Booking confirmed! Your booking ID is {booking['booking_id']}. Total amount: ₹{booking['total_amount']}."
                return {
                    "intent": ConversationIntent.BOOK,
                    "response_type": "booking_success",
                    "response": response,
                    "booking": booking,
                    "needs_action": False
                }
            else:
                return {
                    "intent": ConversationIntent.BOOK,
                    "response_type": "error",
                    "response": "❌ Booking failed. Please try again.",
                    "needs_action": False
                }
                
        except Exception as e:
            logger.error(f"Booking error: {str(e)}")
            return {
                "intent": ConversationIntent.BOOK,
                "response_type": "error",
                "response": f"❌ Booking error: {str(e)}",
                "needs_action": False
            }
    
    def _handle_confirmation_intent(self, user_input: str) -> Dict[str, Any]:
        """Handle booking confirmation"""
        if not self.memory.state.selected_hotel:
            response = "No hotel selected for booking. Please select a hotel first."
            return {
                "intent": ConversationIntent.CONFIRMATION,
                "response_type": "error",
                "response": response,
                "needs_action": False
            }
        
        # Process booking
        from services.booking_service import BookingService
        booking_service = BookingService()
        
        try:
            booking = booking_service.create_booking(
                self.memory.state.selected_hotel,
                self.memory.state.filters
            )
            
            response = self._generate_booking_success(booking)
            
            # Reset context for new booking
            self.memory.reset_context()
            
            return {
                "intent": ConversationIntent.CONFIRMATION,
                "response_type": "booking_success",
                "response": response,
                "booking": booking,
                "needs_action": True
            }
            
        except Exception as e:
            logger.error(f"Booking failed: {str(e)}")
            response = "I apologize, but there was an issue with your booking. Please try again."
            return {
                "intent": ConversationIntent.CONFIRMATION,
                "response_type": "error",
                "response": response,
                "needs_action": False
            }
    
    def _handle_help_intent(self, user_input: str) -> Dict[str, Any]:
        """Handle help intent with contextual assistance"""
        user_input_lower = user_input.lower()
        
        # Check for specific help requests
        if any(word in user_input_lower for word in ["history", "status", "details", "check", "view"]):
            response = self._handle_booking_history_request(user_input)
        elif any(word in user_input_lower for word in ["booking", "reservation"]):
            response = "I can help you with booking hotels. Here's what I can do:\n\n" \
                      "🔍 **Search Hotels**: Tell me your location, budget, and preferences\n" \
                      "📋 **Book Hotels**: Select a hotel and I'll help you complete the booking\n" \
                      "🔄 **Modify Search**: Ask for cheaper, better, or different options\n\n" \
                      "Try: 'Find me a hotel in Bangalore under 5000'"
        else:
            response = self._generate_help_response()
        
        return {
            "intent": ConversationIntent.HELP,
            "response_type": "help",
            "response": response,
            "needs_action": False
        }
    
    def _handle_booking_history_request(self, user_input: str) -> str:
        """Handle booking history and status requests"""
        try:
            from services.booking_service import BookingService
            booking_service = BookingService()
            
            # Get all bookings
            bookings = booking_service.get_all_bookings()
            
            if not bookings:
                return "You don't have any booking history yet. Would you like to search for hotels and make a booking?"
            
            response = f"📋 **Your Booking History** ({len(bookings)} bookings)\n\n"
            
            for booking in bookings[-5:]:  # Show last 5 bookings
                response += f"🏨 **{booking['hotel_name']}** - {booking['location']}\n"
                response += f"🆔 Booking ID: {booking['booking_id']}\n"
                response += f"📅 {booking['check_in']} to {booking['check_out']} ({booking['nights']} nights)\n"
                response += f"💰 Total: ₹{booking['total_amount']} - Status: {booking['status'].title()}\n\n"
            
            response += "Need more details? Ask me about a specific booking ID or search for new hotels."
            return response
            
        except Exception as e:
            logger.error(f"Error getting booking history: {str(e)}")
            return "I'm having trouble accessing your booking history right now. Please try again later or contact support."
    
    def _handle_unknown_intent(self, user_input: str) -> Dict[str, Any]:
        """Handle unknown/intent"""
        # Try to extract any useful information
        from models.llm import extract_user_preferences
        preferences = extract_user_preferences(user_input)
        
        if preferences.get("location"):
            # If we got a location, treat as search
            return self._handle_search_intent(user_input)
        
        response = "I'm here to help you find and book hotels. You can tell me about your preferences like location, budget, and dates. For example: 'Find me a hotel in Bangalore under 5000'"
        
        return {
            "intent": ConversationIntent.UNKNOWN,
            "response_type": "help",
            "response": response,
            "needs_action": False
        }
    
    def _validate_and_normalize(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize user preferences"""
        normalized = preferences.copy()
        
        # Normalize location
        if normalized.get("location"):
            location = normalized["location"].lower()
            location_mapping = {
                "bengaluru": "bangalore",
                "new delhi": "delhi",
                "bombay": "mumbai"
            }
            normalized["location"] = location_mapping.get(location, location.title())
        
        # Validate budget
        if normalized.get("budget") and normalized["budget"] < 500:
            normalized["budget"] = 500  # Minimum reasonable budget
        
        # Validate guests
        if normalized.get("guests") and normalized["guests"] > 10:
            normalized["guests"] = 10  # Maximum reasonable guests
        
        # Ensure preferences is a list
        if normalized.get("preferences") and not isinstance(normalized["preferences"], list):
            normalized["preferences"] = [normalized["preferences"]]
        
        return normalized
    
    def _extract_hotel_selection(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Extract hotel selection from user input"""
        user_input_lower = user_input.lower()
        
        # Check for number-based selection
        import re
        number_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*(?:hotel|option)', user_input_lower)
        if number_match and self.memory.state.last_results:
            index = int(number_match.group(1)) - 1
            if 0 <= index < len(self.memory.state.last_results):
                return self.memory.state.last_results[index]
        
        # Check for ordinal selection
        ordinal_mapping = {
            "first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4
        }
        for ordinal, index in ordinal_mapping.items():
            if ordinal in user_input_lower and self.memory.state.last_results:
                if index < len(self.memory.state.last_results):
                    return self.memory.state.last_results[index]
        
        # Check for name-based selection
        if self.memory.state.last_results:
            for hotel in self.memory.state.last_results:
                hotel_name = hotel["name"].lower()
                if hotel_name in user_input_lower:
                    return hotel
        
        return None
    
    def _generate_search_response(self, hotels: List[Dict], preferences: Dict) -> str:
        """Generate intelligent search response"""
        if not hotels:
            return self._handle_no_results(preferences)
        
        response = f"I found {len(hotels)} great options for you"
        
        if preferences.get("location"):
            response += f" in {preferences['location']}"
        
        if preferences.get("budget"):
            response += f" within your budget of ₹{preferences['budget']}"
        
        response += ". Here are the top recommendations:\n\n"
        
        for i, hotel in enumerate(hotels[:3], 1):
            response += f"{i}. **{hotel['name']}** - {hotel['location']}\n"
            response += f"   💰 ₹{hotel['price_per_night']}/night ⭐ {hotel['rating']}\n"
            
            # Highlight matching preferences
            matching_amenities = []
            user_prefs = preferences.get("preferences", [])
            hotel_amenities = hotel.get("amenities", [])
            
            for pref in user_prefs:
                if pref in hotel_amenities:
                    matching_amenities.append(pref)
            
            if matching_amenities:
                response += f"   ✅ Has: {', '.join(matching_amenities)}\n"
            
            response += "\n"
        
        response += "Would you like more details about any of these hotels, or shall I help you book one?"
        
        return response
    
    def _generate_refinement_response(self, hotels: List[Dict], refinements: Dict) -> str:
        """Generate refinement response"""
        response = "I've refined the search results based on your preferences.\n\n"
        
        if refinements.get("budget"):
            response += f"💰 Budget adjusted to ₹{refinements['budget']}\n"
        
        if refinements.get("preferences"):
            response += f"🎯 Added preferences: {', '.join(refinements['preferences'])}\n"
        
        response += f"\nFound {len(hotels)} matching hotels:\n\n"
        
        for i, hotel in enumerate(hotels[:3], 1):
            response += f"{i}. **{hotel['name']}** - ₹{hotel['price_per_night']}/night ⭐ {hotel['rating']}\n"
        
        response += "\nWould you like to book one of these or refine further?"
        
        return response
    
    def _generate_booking_confirmation(self, hotel: Dict) -> str:
        """Generate booking confirmation message"""
        nights = self.memory.state.filters.get("nights", 1)
        total_cost = hotel["price_per_night"] * nights
        
        response = f"Ready to book **{hotel['name']}**?\n\n"
        response += f"📍 Location: {hotel['location']}\n"
        response += f"💰 Price: ₹{hotel['price_per_night']}/night\n"
        response += f"🌙 Nights: {nights}\n"
        response += f"💵 Total: ₹{total_cost}\n\n"
        response += "Please confirm to proceed with the booking."
        
        return response
    
    def _generate_booking_success(self, booking: Dict) -> str:
        """Generate booking success message"""
        response = f"🎉 **Booking Confirmed!**\n\n"
        response += f"🆔 Booking ID: {booking['booking_id']}\n"
        response += f"🏨 Hotel: {booking['hotel_name']}\n"
        response += f"📅 Check-in: {booking['check_in']}\n"
        response += f"📅 Check-out: {booking['check_out']}\n"
        response += f"👥 Guests: {booking['guests']}\n"
        response += f"💰 Total: ₹{booking['total_amount']}\n\n"
        response += "You'll receive a confirmation email shortly. Is there anything else I can help you with?"
        
        return response
    
    def _generate_help_response(self) -> str:
        """Generate help response"""
        response = "I'm your AI Hotel Booking Assistant! Here's how I can help you:\n\n"
        response += "🔍 **Search**: Tell me your preferences (location, budget, dates, guests)\n"
        response += "🎯 **Refine**: Ask for cheaper options, specific amenities, or different locations\n"
        response += "📋 **Book**: Select a hotel and I'll help you complete the booking\n\n"
        response += "**Examples:**\n"
        response += "• 'Find me a hotel in Bangalore under 5000'\n"
        response += "• 'Show me hotels with pool in Goa'\n"
        response += "• 'Book the first option'\n\n"
        response += "What would you like to do?"
        
        return response
    
    def _ask_for_clarification(self) -> str:
        """Ask for clarification when intent is unclear"""
        response = "I'd like to help you better. Could you please clarify:\n\n"
        response += "• Are you looking for cheaper options?\n"
        response += "• Do you want specific amenities (pool, wifi, etc.)?\n"
        response += "• Would you like to see hotels in a different location?\n\n"
        response += "Please let me know what you'd like to refine!"
        
        return response
    
    def _handle_no_results(self, preferences: Dict) -> Dict[str, Any]:
        """Handle no search results intelligently"""
        suggestions = []
        
        if preferences.get("budget"):
            suggestions.append(f"Try increasing your budget above ₹{preferences['budget'] + 1000}")
        
        if preferences.get("location"):
            nearby_cities = self._get_nearby_cities(preferences["location"])
            if nearby_cities:
                suggestions.append(f"Check nearby cities: {', '.join(nearby_cities)}")
        
        if preferences.get("preferences"):
            suggestions.append("Remove some amenity preferences to see more options")
        
        response = "I couldn't find hotels matching your criteria. Here are some suggestions:\n\n"
        for suggestion in suggestions:
            response += f"• {suggestion}\n"
        
        response += "\nWould you like me to try with adjusted criteria?"
        
        return {
            "intent": ConversationIntent.SEARCH,
            "response_type": "no_results",
            "response": response,
            "hotels": [],
            "needs_action": False
        }
    
    def _get_nearby_cities(self, location: str) -> List[str]:
        """Get nearby cities for suggestions"""
        nearby_mapping = {
            "Bangalore": ["Mysore", "Hosur", "Tumkur"],
            "Mumbai": ["Pune", "Navi Mumbai", "Thane"],
            "Delhi": ["Gurgaon", "Noida", "Faridabad"],
            "Goa": ["Panjim", "Margao", "Vasco"],
            "Chennai": ["Coimbatore", "Bangalore", "Pondicherry"]
        }
        
        return nearby_mapping.get(location, [])
    
    def update_memory_after_response(self, response: str):
        """Update memory after generating response"""
        if self.memory.state.conversation_history:
            last_exchange = self.memory.state.conversation_history[-1]
            last_exchange["assistant_response"] = response
            last_exchange["timestamp"] = self.memory.state.last_updated
