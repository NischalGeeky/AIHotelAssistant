import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from utils.memory import ConversationIntent
from services.enhanced_hotel_service import EnhancedHotelService
from services.booking_service import BookingService
from utils.validation import InputValidator

logger = logging.getLogger(__name__)

class ToolType(Enum):
    SEARCH_HOTELS = "search_hotels"
    EXTRACT_PREFERENCES = "extract_preferences"
    BOOK_HOTEL = "book_hotel"
    GET_HOTEL_DETAILS = "get_hotel_details"
    GET_BOOKING_DETAILS = "get_booking_details"
    CANCEL_BOOKING = "cancel_booking"
    GET_RECOMMENDATIONS = "get_recommendations"
    VALIDATE_INPUT = "validate_input"

class ToolRouter:
    """Strict tool routing layer for deterministic operations"""
    
    def __init__(self):
        self.enhanced_hotel_service = EnhancedHotelService()
        self.booking_service = BookingService()
        self.validator = InputValidator()
        
        # Define routing rules
        self.routing_rules = {
            ConversationIntent.SEARCH: [ToolType.VALIDATE_INPUT, ToolType.EXTRACT_PREFERENCES, ToolType.SEARCH_HOTELS],
            ConversationIntent.REFINE: [ToolType.VALIDATE_INPUT, ToolType.SEARCH_HOTELS],
            ConversationIntent.BOOK: [ToolType.VALIDATE_INPUT, ToolType.BOOK_HOTEL],
            ConversationIntent.CONFIRMATION: [ToolType.BOOK_HOTEL],
            ConversationIntent.HELP: [],
            ConversationIntent.UNKNOWN: [ToolType.VALIDATE_INPUT, ToolType.EXTRACT_PREFERENCES]
        }
        
        # Tool execution registry
        self.tools = {
            ToolType.SEARCH_HOTELS: self._search_hotels,
            ToolType.EXTRACT_PREFERENCES: self._extract_preferences,
            ToolType.BOOK_HOTEL: self._book_hotel,
            ToolType.GET_HOTEL_DETAILS: self._get_hotel_details,
            ToolType.GET_BOOKING_DETAILS: self._get_booking_details,
            ToolType.CANCEL_BOOKING: self._cancel_booking,
            ToolType.GET_RECOMMENDATIONS: self._get_recommendations,
            ToolType.VALIDATE_INPUT: self._validate_input
        }
    
    def route_and_execute(self, intent: ConversationIntent, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route and execute tools based on intent with strict deterministic behavior
        
        Args:
            intent: Detected user intent
            user_input: Raw user input
            context: Current conversation context
            
        Returns:
            Tool execution result
        """
        logger.info(f"Routing intent: {intent.value}")
        
        # Get required tools for this intent
        required_tools = self.routing_rules.get(intent, [])
        
        if not required_tools:
            return {
                "success": True,
                "response_type": "help",
                "response": self._get_help_response(intent),
                "data": None
            }
        
        # Execute tools in sequence
        execution_context = context.copy()
        execution_context["user_input"] = user_input
        
        for tool_type in required_tools:
            logger.info(f"Executing tool: {tool_type.value}")
            
            try:
                result = self.tools[tool_type](execution_context)
                
                if not result.get("success", False):
                    logger.error(f"Tool {tool_type.value} failed: {result.get('error', 'Unknown error')}")
                    return {
                        "success": False,
                        "response_type": "error",
                        "response": result.get("error", "An error occurred"),
                        "data": None
                    }
                
                # Update context with tool results
                execution_context.update(result.get("data", {}))
                
            except Exception as e:
                logger.error(f"Tool {tool_type.value} execution failed: {str(e)}")
                return {
                    "success": False,
                    "response_type": "error",
                    "response": f"An error occurred while processing your request: {str(e)}",
                    "data": None
                }
        
        # Generate final response based on execution results
        final_response = self._generate_final_response(intent, execution_context)
        
        return {
            "success": True,
            "response_type": final_response["type"],
            "response": final_response["content"],
            "data": execution_context
        }
    
    def _validate_input(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user input"""
        user_input = context.get("user_input", "")
        
        validation_result = self.validator.validate_search_input(user_input)
        
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": validation_result["error"],
                "data": {}
            }
        
        return {
            "success": True,
            "data": {
                "validated_input": validation_result["normalized"],
                "extracted_entities": validation_result["entities"]
            }
        }
    
    def _extract_preferences(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user preferences"""
        user_input = context.get("user_input", "")
        
        from models.llm import extract_user_preferences
        
        try:
            preferences = extract_user_preferences(user_input)
            
            # Validate and normalize preferences
            validated_preferences = self.validator.validate_preferences(preferences)
            
            return {
                "success": True,
                "data": {
                    "preferences": validated_preferences,
                    "missing_fields": self._get_missing_fields(validated_preferences)
                }
            }
            
        except Exception as e:
            logger.error(f"Preference extraction failed: {str(e)}")
            return {
                "success": False,
                "error": "I couldn't understand your preferences. Could you please rephrase your request?",
                "data": {}
            }
    
    def _search_hotels(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search for hotels using enhanced service"""
        preferences = context.get("preferences", {})
        
        if not preferences.get("location"):
            return {
                "success": False,
                "error": "I need to know which location you're looking for. Could you please specify the city?",
                "data": {}
            }
        
        try:
            hotels = self.enhanced_hotel_service.search_hotels_hybrid(preferences)
            
            if not hotels:
                # Get smart recommendations
                recommendations = self.enhanced_hotel_service.get_smart_recommendations(preferences, [])
                
                return {
                    "success": True,
                    "data": {
                        "hotels": [],
                        "recommendations": recommendations,
                        "no_results": True
                    }
                }
            
            # Get recommendations for found hotels
            recommendations = self.enhanced_hotel_service.get_smart_recommendations(preferences, hotels)
            
            return {
                "success": True,
                "data": {
                    "hotels": hotels,
                    "recommendations": recommendations,
                    "no_results": False
                }
            }
            
        except Exception as e:
            logger.error(f"Hotel search failed: {str(e)}")
            return {
                "success": False,
                "error": "I encountered an error while searching for hotels. Please try again.",
                "data": {}
            }
    
    def _book_hotel(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Book a hotel with validation"""
        preferences = context.get("preferences", {})
        selected_hotel = context.get("selected_hotel")
        
        if not selected_hotel:
            # Try to extract hotel selection from context
            hotels = context.get("hotels", [])
            if hotels:
                selected_hotel = hotels[0]  # Default to first hotel
            else:
                return {
                    "success": False,
                    "error": "No hotel selected for booking. Please select a hotel first.",
                    "data": {}
                }
        
        # Validate booking requirements
        missing_fields = self._get_missing_booking_fields(preferences)
        if missing_fields:
            return {
                "success": False,
                "error": f"I need more information to complete the booking: {', '.join(missing_fields)}",
                "data": {}
            }
        
        try:
            booking = self.booking_service.create_booking(selected_hotel, preferences)
            
            return {
                "success": True,
                "data": {
                    "booking": booking,
                    "booking_confirmed": True
                }
            }
            
        except Exception as e:
            logger.error(f"Booking failed: {str(e)}")
            return {
                "success": False,
                "error": "I apologize, but there was an issue with your booking. Please try again.",
                "data": {}
            }
    
    def _get_hotel_details(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed hotel information"""
        hotel_id = context.get("hotel_id")
        
        if not hotel_id:
            return {
                "success": False,
                "error": "Hotel ID not provided",
                "data": {}
            }
        
        hotel = self.enhanced_hotel_service.get_hotel_by_id(hotel_id)
        
        if not hotel:
            return {
                "success": False,
                "error": "Hotel not found",
                "data": {}
            }
        
        return {
            "success": True,
            "data": {
                "hotel": hotel
            }
        }
    
    def _get_booking_details(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get booking details"""
        booking_id = context.get("booking_id")
        
        if not booking_id:
            return {
                "success": False,
                "error": "Booking ID not provided",
                "data": {}
            }
        
        booking = self.booking_service.get_booking_by_id(booking_id)
        
        if not booking:
            return {
                "success": False,
                "error": "Booking not found",
                "data": {}
            }
        
        return {
            "success": True,
            "data": {
                "booking": booking
            }
        }
    
    def _cancel_booking(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a booking"""
        booking_id = context.get("booking_id")
        
        if not booking_id:
            return {
                "success": False,
                "error": "Booking ID not provided",
                "data": {}
            }
        
        success = self.booking_service.cancel_booking(booking_id)
        
        if not success:
            return {
                "success": False,
                "error": "Failed to cancel booking",
                "data": {}
            }
        
        return {
            "success": True,
            "data": {
                "booking_cancelled": True
            }
        }
    
    def _get_recommendations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get smart recommendations"""
        preferences = context.get("preferences", {})
        hotels = context.get("hotels", [])
        
        recommendations = self.enhanced_hotel_service.get_smart_recommendations(preferences, hotels)
        
        return {
            "success": True,
            "data": {
                "recommendations": recommendations
            }
        }
    
    def _generate_final_response(self, intent: ConversationIntent, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final response based on execution results"""
        hotels = context.get("hotels", [])
        recommendations = context.get("recommendations", {})
        booking = context.get("booking")
        no_results = context.get("no_results", False)
        
        if intent == ConversationIntent.SEARCH:
            if no_results:
                return {
                    "type": "no_results",
                    "content": self._generate_no_results_response(recommendations)
                }
            else:
                return {
                    "type": "search_results",
                    "content": self._generate_search_response(hotels, context.get("preferences", {}))
                }
        
        elif intent == ConversationIntent.REFINE:
            if no_results:
                return {
                    "type": "no_results",
                    "content": self._generate_no_results_response(recommendations)
                }
            else:
                return {
                    "type": "refined_results",
                    "content": self._generate_refinement_response(hotels, context.get("preferences", {}))
                }
        
        elif intent == ConversationIntent.BOOK:
            if booking:
                return {
                    "type": "booking_success",
                    "content": self._generate_booking_success_response(booking)
                }
            else:
                return {
                    "type": "booking_confirmation",
                    "content": self._generate_booking_confirmation_response(context.get("selected_hotel"))
                }
        
        elif intent == ConversationIntent.CONFIRMATION:
            if booking:
                return {
                    "type": "booking_success",
                    "content": self._generate_booking_success_response(booking)
                }
        
        else:
            return {
                "type": "help",
                "content": self._get_help_response(intent)
            }
    
    def _generate_search_response(self, hotels: List[Dict], preferences: Dict) -> str:
        """Generate search response"""
        if not hotels:
            return "I couldn't find any hotels matching your criteria."
        
        response = f"I found {len(hotels)} great options for you"
        
        if preferences.get("location"):
            response += f" in {preferences['location']}"
        
        response += ". Here are the top recommendations:\n\n"
        
        for i, hotel in enumerate(hotels[:3], 1):
            response += f"{i}. **{hotel['name']}** - {hotel['location']}\n"
            response += f"   💰 ₹{hotel['price_per_night']}/night ⭐ {hotel['rating']}\n"
            
            # Add semantic explanation
            explanation = self.enhanced_hotel_service.get_semantic_explanation(hotel, preferences, 0.8)
            response += f"   📝 {explanation}\n\n"
        
        response += "Would you like more details about any of these hotels, or shall I help you book one?"
        
        return response
    
    def _generate_refinement_response(self, hotels: List[Dict], preferences: Dict) -> str:
        """Generate refinement response"""
        response = "I've refined the search results based on your preferences.\n\n"
        response += f"Found {len(hotels)} matching hotels:\n\n"
        
        for i, hotel in enumerate(hotels[:3], 1):
            response += f"{i}. **{hotel['name']}** - ₹{hotel['price_per_night']}/night ⭐ {hotel['rating']}\n"
        
        response += "\nWould you like to book one of these or refine further?"
        
        return response
    
    def _generate_booking_success_response(self, booking: Dict) -> str:
        """Generate booking success response"""
        response = f"🎉 **Booking Confirmed!**\n\n"
        response += f"🆔 Booking ID: {booking['booking_id']}\n"
        response += f"🏨 Hotel: {booking['hotel_name']}\n"
        response += f"📅 Check-in: {booking['check_in']}\n"
        response += f"📅 Check-out: {booking['check_out']}\n"
        response += f"👥 Guests: {booking['guests']}\n"
        response += f"💰 Total: ₹{booking['total_amount']}\n\n"
        response += "You'll receive a confirmation email shortly. Is there anything else I can help you with?"
        
        return response
    
    def _generate_booking_confirmation_response(self, hotel: Dict) -> str:
        """Generate booking confirmation response"""
        if not hotel:
            return "No hotel selected for booking."
        
        response = f"Ready to book **{hotel['name']}**?\n\n"
        response += f"📍 Location: {hotel['location']}\n"
        response += f"💰 Price: ₹{hotel['price_per_night']}/night\n"
        response += f"⭐ Rating: {hotel['rating']}\n\n"
        response += "Please confirm to proceed with the booking."
        
        return response
    
    def _generate_no_results_response(self, recommendations: Dict) -> str:
        """Generate no results response with recommendations"""
        response = "I couldn't find hotels matching your criteria. Here are some suggestions:\n\n"
        
        if recommendations.get("nearby_cities"):
            response += f"📍 **Nearby cities**: {', '.join(recommendations['nearby_cities'])}\n"
        
        if recommendations.get("price_alternatives"):
            response += f"💰 **Price alternatives**: Try adjusting your budget range\n"
        
        if recommendations.get("amenity_alternatives"):
            response += f"🎯 **Alternative amenities**: Consider different amenities\n"
        
        response += "\nWould you like me to try with adjusted criteria?"
        
        return response
    
    def _get_help_response(self, intent: ConversationIntent) -> str:
        """Get help response"""
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
    
    def _get_missing_fields(self, preferences: Dict[str, Any]) -> List[str]:
        """Get missing required fields"""
        missing = []
        
        if not preferences.get("location"):
            missing.append("location")
        
        if not preferences.get("guests"):
            missing.append("number of guests")
        
        return missing
    
    def _get_missing_booking_fields(self, preferences: Dict[str, Any]) -> List[str]:
        """Get missing fields required for booking"""
        missing = []
        
        if not preferences.get("location"):
            missing.append("location")
        
        if not preferences.get("guests"):
            missing.append("number of guests")
        
        if not preferences.get("nights") and not preferences.get("check_in"):
            missing.append("dates or number of nights")
        
        return missing
