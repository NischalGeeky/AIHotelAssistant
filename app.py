import streamlit as st
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from models.llm import get_llm_response, extract_user_preferences, chat_with_context
from services.hotel_service import HotelService
from services.booking_service import BookingService
from services.enhanced_hotel_service import EnhancedHotelService
from utils.parser import parse_booking_request
from utils.prompts import get_system_prompt
from utils.tools import execute_tool, format_tools_for_llm, AVAILABLE_TOOLS
from utils.memory import ConversationMemory
from utils.intelligence import ConversationIntelligence
from utils.router import ToolRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize enhanced services
hotel_service = EnhancedHotelService()
booking_service = BookingService()
conversation_intelligence = ConversationIntelligence(hotel_service)
tool_router = ToolRouter()

# Import monitoring
from utils.monitoring import get_monitoring_service, track_performance
monitoring_service = get_monitoring_service()

def safe_get_nights(preferences: Dict[str, Any]) -> int:
    """Safely get nights value with proper None handling"""
    if not preferences:
        return 1
    nights = preferences.get('nights')
    return nights if nights is not None else 1

# Session state initialization
def init_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'conversation_intelligence' not in st.session_state:
        st.session_state.conversation_intelligence = conversation_intelligence
    if 'selected_hotel' not in st.session_state:
        st.session_state.selected_hotel = None
    if 'booking_info' not in st.session_state:
        st.session_state.booking_info = {}
    if 'show_booking_summary' not in st.session_state:
        st.session_state.show_booking_summary = False

def display_enhanced_hotel_card(hotel: Dict, index: int, preferences: Dict = None):
    """Display enhanced hotel card with images and actions"""
    with st.container():
        # Create card with border
        st.markdown("""
        <style>
        .hotel-card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .hotel-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .price-tag {
            background: #ff6b6b;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        .rating-badge {
            background: #4ecdc4;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Hotel image (placeholder)
        image_url = f"https://picsum.photos/seed/hotel{hotel['id']}/400/250.jpg"
        
        with st.container():
            col1, col2 = st.columns([3, 2])
            
            with col1:
                # Hotel image
                st.image(image_url, use_column_width=True)
                
                # Hotel name and rating
                st.markdown(f"### 🏨 {hotel['name']}")
                
                # Rating and badges
                rating_col1, rating_col2, rating_col3 = st.columns(3)
                with rating_col1:
                    st.markdown(f'<div class="rating-badge">⭐ {hotel["rating"]}</div>', unsafe_allow_html=True)
                with rating_col2:
                    st.markdown(f'<div class="price-tag">💰 ₹{hotel["price_per_night"]}</div>', unsafe_allow_html=True)
                with rating_col3:
                    category_badge = hotel.get('category', 'mid-range').title()
                    st.markdown(f'<div style="background: #95a5a6; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{category_badge}</div>', unsafe_allow_html=True)
                
                # Location
                st.markdown(f"📍 **{hotel['location']}**")
                
                # Description
                if hotel.get('description'):
                    st.markdown(f"*{hotel['description']}*")
                
                # Amenities with icons
                st.markdown("**Amenities:**")
                amenity_icons = {
                    'wifi': '🌐',
                    'pool': '🏊',
                    'breakfast': '🍳',
                    'ac': '❄️',
                    'parking': '🚗',
                    'gym': '💪',
                    'spa': '�',
                    'restaurant': '🍽️',
                    'beach_access': '🏖️',
                    'mountain_view': '🏔️'
                }
                
                amenities_cols = st.columns(4)
                for i, amenity in enumerate(hotel.get('amenities', [])[:8]):
                    icon = amenity_icons.get(amenity, '✅')
                    with amenities_cols[i % 4]:
                        st.markdown(f"{icon} {amenity.title()}")
            
            with col2:
                # Price calculation
                nights = safe_get_nights(preferences)
                total_cost = hotel['price_per_night'] * nights
                
                st.markdown("### 💰 Pricing")
                st.markdown(f"**Per Night:** ₹{hotel['price_per_night']}")
                st.markdown(f"**{nights} Night{'s' if nights != 1 else ''}:** ₹{total_cost}")
                
                # Semantic explanation if available
                if preferences:
                    explanation = hotel_service.get_semantic_explanation(hotel, preferences, 0.8)
                    st.markdown("### � Why this hotel?")
                    st.markdown(f"*{explanation}*")
                
                # Action buttons
                st.markdown("### 🎯 Actions")
                
                if st.button(f"📋 Book Now", key=f"book_{index}", use_container_width=True, type="primary"):
                    st.session_state.selected_hotel = hotel
                    # Update conversation intelligence memory
                    st.session_state.conversation_intelligence.memory.state.selected_hotel = hotel
                    if preferences:
                        st.session_state.conversation_intelligence.memory.state.filters.update(preferences)
                    st.session_state.show_booking_summary = True
                    st.rerun()
                
                if st.button(f"🔍 More Details", key=f"details_{index}", use_container_width=True):
                    st.session_state.selected_hotel = hotel
                    st.rerun()
                
                if st.button(f"❤️ Save", key=f"save_{index}", use_container_width=True):
                    st.success(f"{hotel['name']} saved to favorites!")
                
                # Reviews placeholder
                st.markdown("### 📝 Reviews")
                st.markdown("⭐⭐⭐⭐⭐ *Excellent location and service*")
                st.markdown("⭐⭐⭐⭐ *Great value for money*")
        
        st.markdown("---")

def display_booking_summary_panel():
    """Display booking summary panel in sidebar"""
    if st.session_state.show_booking_summary and st.session_state.selected_hotel:
        with st.sidebar:
            st.markdown("### 📋 Booking Summary")
            
            hotel = st.session_state.selected_hotel
            preferences = st.session_state.conversation_intelligence.memory.state.filters
            
            # Hotel details
            st.markdown(f"**🏨 {hotel['name']}**")
            st.markdown(f"📍 {hotel['location']}")
            st.markdown(f"⭐ {hotel['rating']}")
            
            st.markdown("---")
            
            # Booking details
            nights = safe_get_nights(preferences)
            total_cost = hotel['price_per_night'] * nights
            
            st.markdown("### 💰 Cost Breakdown")
            st.markdown(f"Rate: ₹{hotel['price_per_night']}/night")
            st.markdown(f"Nights: {nights}")
            st.markdown(f"**Total: ₹{total_cost}**")
            
            st.markdown("---")
            
            # Guest details
            st.markdown("### 👥 Guests")
            guests = preferences.get('guests', 1)
            st.markdown(f"Adults: {guests}")
            
            st.markdown("---")
            
            # Preferences
            if preferences.get('preferences'):
                st.markdown("### 🎯 Preferences")
                for pref in preferences['preferences']:
                    st.markdown(f"✅ {pref.title()}")
            
            st.markdown("---")
            
            # Action buttons
            if st.button("📋 Confirm Booking", use_container_width=True, type="primary"):
                # Process booking directly using booking service
                try:
                    booking_preferences = preferences.copy()
                    booking_preferences.update({
                        'hotel_id': hotel.get('id'),
                        'check_in': booking_preferences.get('check_in'),
                        'check_out': booking_preferences.get('check_out'),
                        'nights': safe_get_nights(preferences),
                        'guests': preferences.get('guests', 1)
                    })
                    
                    # Create booking
                    booking = booking_service.create_booking(hotel, booking_preferences)
                    
                    if booking:
                        st.session_state.booking_info = booking
                        st.session_state.show_booking_summary = False
                        st.session_state.selected_hotel = None
                        st.success("🎉 Booking confirmed successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Booking failed. Please try again.")
                        
                except Exception as e:
                    st.error(f"❌ Booking error: {str(e)}")
                    logger.error(f"Booking error: {str(e)}")
            
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_booking_summary = False
                st.session_state.selected_hotel = None
                st.rerun()

def display_smart_recommendations(recommendations: Dict):
    """Display smart recommendations in sidebar"""
    with st.sidebar:
        st.markdown("### 💡 Smart Suggestions")
        
        if recommendations.get("nearby_cities"):
            st.markdown("**📍 Nearby Cities:**")
            for city in recommendations["nearby_cities"]:
                if st.button(f"🔍 {city}", key=f"nearby_{city}"):
                    st.session_state.conversation_intelligence.memory.state.filters["location"] = city
                    st.rerun()
        
        if recommendations.get("price_alternatives"):
            st.markdown("**💰 Price Alternatives:**")
            st.markdown("• Try adjusting your budget range")
            st.markdown("• Consider different dates")
        
        if recommendations.get("amenity_alternatives"):
            st.markdown("**🎯 Alternative Amenities:**")
            st.markdown("• Different amenities might have more options")
            st.markdown("• Try removing some preferences")

def display_enhanced_chat_ui():
    """Display enhanced chat interface with typing indicator"""
    # Chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Typing indicator (simulated)
    if st.session_state.get("typing", False):
        with st.chat_message("assistant"):
            st.markdown("🤔 *Thinking...*")
    
    # Enhanced chat input
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            prompt = st.chat_input("What kind of hotel are you looking for?", key="main_chat")
        
        with col2:
            if st.button("🎤", help="Voice input (coming soon)"):
                st.info("Voice input coming soon!")
    
    return prompt

def display_booking_confirmation(booking_info: Dict):
    """Display booking confirmation card"""
    with st.container():
        # Success message
        st.success("🎉 Booking Successfully Confirmed!", icon="✅")
        
        # Booking details card
        with st.expander("📋 Booking Details", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### Booking Information")
                st.markdown(f"**🆔 Booking ID:** `{booking_info['booking_id']}`")
                st.markdown(f"**🏨 Hotel:** {booking_info['hotel_name']}")
                st.markdown(f"**📍 Location:** {booking_info['hotel_location']}")
                st.markdown(f"**👥 Guests:** {booking_info['guests']}")
                st.markdown(f"**📅 Check-in:** {booking_info['check_in']}")
                st.markdown(f"**📅 Check-out:** {booking_info['check_out']}")
                st.markdown(f"**🌙 Nights:** {booking_info['nights']}")
                
                if booking_info.get('preferences'):
                    st.markdown("**🎯 Preferences:**")
                    for pref in booking_info['preferences']:
                        st.markdown(f"• {pref.title()}")
            
            with col2:
                st.markdown("### 💰 Payment Summary")
                st.markdown(f"**Rate:** ₹{booking_info['price_per_night']}/night")
                st.markdown(f"**Nights:** {booking_info['nights']}")
                st.markdown("---")
                st.markdown(f"### **Total: ₹{booking_info['total_amount']}**")
                st.markdown(f"**Status:** ✅ {booking_info['status'].title()}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏠 Start New Booking", use_container_width=True, type="primary"):
                reset_booking_state()
                st.rerun()
        
        with col2:
            if st.button("📧 Email Confirmation", use_container_width=True):
                st.info("Confirmation email sent successfully!")
        
        with col3:
            if st.button("📱 Download Receipt", use_container_width=True):
                st.info("Receipt downloaded to your device!")
        
        # Additional information
        st.markdown("---")
        st.markdown("### 📞 Need Help?")
        st.markdown("Contact our 24/7 customer support:")
        st.markdown("📧 support@hotelbooking.ai | 📞 1800-123-4567")

def reset_booking_state():
    """Reset booking session state"""
    st.session_state.booking_stage = 'search'
    st.session_state.extracted_preferences = {}
    st.session_state.shortlisted_hotels = []
    st.session_state.selected_hotel = None
    st.session_state.booking_info = {}

@track_performance("chat_response")
def get_enhanced_chat_response(user_input: str) -> Dict[str, Any]:
    """Process user input using enhanced conversation intelligence"""
    try:
        # Show typing indicator
        st.session_state.typing = True
        
        # Process with conversation intelligence
        result = st.session_state.conversation_intelligence.process_user_input(user_input)
        
        return result
    
    except Exception as e:
        logger.error(f"Error in enhanced chat response: {str(e)}")
        return {
            "intent": "error",
            "response_type": "error",
            "response": "I apologize, but I encountered an error. Please try again.",
            "needs_action": False
        }
    finally:
        # Hide typing indicator
        st.session_state.typing = False

def reset_booking_state():
    """Reset booking session state"""
    st.session_state.conversation_intelligence.memory.reset_context()
    st.session_state.selected_hotel = None
    st.session_state.booking_info = {}
    st.session_state.show_booking_summary = False

def main():
    st.set_page_config(
        page_title="AI Hotel Booking Assistant - Premium",
        page_icon="🏨",
        layout="wide",
        initial_sidebar_state="auto"
    )
    
    # Custom CSS for enhanced UI
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .chat-container {
        height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced header
    st.markdown("""
    <div class="main-header">
        <h1>🏨 AI Hotel Booking Assistant</h1>
        <p>✨ Find and book the perfect hotel with AI-powered intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    init_session_state()
    
    # Main layout
    main_col, sidebar_col = st.columns([3, 1])
    
    with sidebar_col:
        # Booking summary panel
        display_booking_summary_panel()
        
        # Smart suggestions
        if hasattr(st.session_state.conversation_intelligence.memory.state, 'last_results') and st.session_state.conversation_intelligence.memory.state.last_results:
            recommendations = hotel_service.get_smart_recommendations(
                st.session_state.conversation_intelligence.memory.state.filters,
                st.session_state.conversation_intelligence.memory.state.last_results
            )
            display_smart_recommendations(recommendations)
        
        # Quick actions
        st.markdown("### 🚀 Quick Actions")
        
        quick_searches = [
            "🏖️ Beach resorts in Goa",
            "💰 Budget hotels in Delhi", 
            "⭐ Luxury hotels in Mumbai",
            "🏔️ Hill stations in Manali"
        ]
        
        for search in quick_searches:
            if st.button(search, key=f"quick_{search}", use_container_width=True):
                # Process quick search
                result = get_enhanced_chat_response(search)
                st.session_state.messages.append({"role": "user", "content": search})
                st.session_state.messages.append({"role": "assistant", "content": result["response"]})
                st.rerun()
    
    with main_col:
        # Enhanced chat interface
        prompt = display_enhanced_chat_ui()
        
        # Display hotel results if available
        if hasattr(st.session_state.conversation_intelligence.memory.state, 'last_results') and st.session_state.conversation_intelligence.memory.state.last_results:
            hotels = st.session_state.conversation_intelligence.memory.state.last_results
            preferences = st.session_state.conversation_intelligence.memory.state.filters
            
            st.markdown("### 🏨 Available Hotels")
            
            for i, hotel in enumerate(hotels):
                display_enhanced_hotel_card(hotel, i, preferences)
        
        # Display booking confirmation if available
        if st.session_state.booking_info:
            display_booking_confirmation(st.session_state.booking_info)
        
        # Handle user input
        if prompt:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get enhanced response
            result = get_enhanced_chat_response(prompt)
            
            # Add assistant response
            st.session_state.messages.append({"role": "assistant", "content": result["response"]})
            
            # Handle special response types
            if result.get("response_type") == "search_results" and result.get("hotels"):
                st.session_state.conversation_intelligence.memory.state.last_results = result["hotels"]
            elif result.get("response_type") == "booking_success" and result.get("booking"):
                st.session_state.booking_info = result["booking"]
            
            # Rerun to update UI
            st.rerun()

if __name__ == "__main__":
    main()
