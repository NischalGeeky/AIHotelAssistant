import streamlit as st
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple hotel booking assistant without heavy ML dependencies
class SimpleHotelAssistant:
    def __init__(self):
        self.hotels = self._load_hotels()
        self.bookings = []
        self.conversation_state = {
            'last_search': None,
            'selected_hotel': None,
            'user_preferences': {}
        }
    
    def _load_hotels(self) -> List[Dict]:
        """Load hotel data"""
        try:
            with open('data/hotels.json', 'r') as f:
                return json.load(f)
        except:
            # Fallback sample data
            return [
                {
                    'id': '1',
                    'name': 'Grand Plaza Hotel',
                    'location': 'Bangalore',
                    'price_per_night': 3500,
                    'rating': 4.5,
                    'amenities': ['wifi', 'pool', 'gym', 'spa']
                },
                {
                    'id': '2', 
                    'name': 'Seaside Resort',
                    'location': 'Goa',
                    'price_per_night': 4500,
                    'rating': 4.8,
                    'amenities': ['wifi', 'beach', 'restaurant', 'bar']
                },
                {
                    'id': '3',
                    'name': 'Mountain View Lodge',
                    'location': 'Manali',
                    'price_per_night': 2500,
                    'rating': 4.2,
                    'amenities': ['wifi', 'mountain_view', 'fireplace']
                }
            ]
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process user query with simple logic"""
        query_lower = query.lower()
        
        # Check for booking history/status requests
        if any(word in query_lower for word in ['history', 'status', 'details', 'check', 'view']):
            if self.bookings:
                response = "📋 **Your Booking History**\n\n"
                for booking in self.bookings[-3:]:  # Show last 3
                    response += f"🏨 {booking['hotel_name']} - {booking['location']}\n"
                    response += f"🆔 ID: {booking['booking_id']}\n"
                    response += f"📅 {booking['check_in']} to {booking['check_out']}\n"
                    response += f"💰 ₹{booking['total_amount']} - {booking['status']}\n\n"
                return {'type': 'history', 'response': response}
            else:
                return {'type': 'history', 'response': 'You have no booking history yet. Search for hotels first!'}
        
        # Check for booking intent
        if any(word in query_lower for word in ['book', 'reserve']) and self.conversation_state['selected_hotel']:
            return self._create_booking()
        
        # Search for hotels
        return self._search_hotels(query)
    
    def _search_hotels(self, query: str) -> Dict[str, Any]:
        """Search hotels based on query"""
        query_lower = query.lower()
        
        # Extract location
        locations = ['bangalore', 'mumbai', 'delhi', 'goa', 'manali', 'kerala']
        location = next((loc for loc in locations if loc in query_lower), None)
        
        if not location:
            return {
                'type': 'clarification',
                'response': 'Which location are you looking for? (Bangalore, Mumbai, Delhi, Goa, Manali, Kerala)'
            }
        
        # Extract budget
        budget = None
        import re
        budget_match = re.search(r'under\s*(\d+)|below\s*(\d+)|(\d+)\s*rupees?|(\d+)\s*rs?|₹(\d+)', query_lower)
        if budget_match:
            budget = int(next(filter(None, budget_match.groups())))
        
        # Filter hotels
        filtered_hotels = []
        for hotel in self.hotels:
            if hotel['location'].lower() == location:
                if budget is None or hotel['price_per_night'] <= budget:
                    filtered_hotels.append(hotel)
        
        if not filtered_hotels:
            return {
                'type': 'no_results',
                'response': f'No hotels found in {location.title()} within your budget.'
            }
        
        # Store search state
        self.conversation_state['last_search'] = filtered_hotels
        self.conversation_state['user_preferences'] = {'location': location, 'budget': budget}
        
        # Generate response
        response = f"I found {len(filtered_hotels)} hotels in {location.title()}"
        if budget:
            response += f" under ₹{budget}"
        response += ":\n\n"
        
        for i, hotel in enumerate(filtered_hotels, 1):
            response += f"{i}. **{hotel['name']}**\n"
            response += f"   💰 ₹{hotel['price_per_night']}/night ⭐ {hotel['rating']}\n"
            response += f"   📍 {hotel['location']}\n"
            response += f"   ✅ {', '.join(hotel['amenities'])}\n\n"
        
        response += "Type 'book hotel [number]' to make a booking."
        
        return {
            'type': 'search_results',
            'hotels': filtered_hotels,
            'response': response
        }
    
    def _create_booking(self) -> Dict[str, Any]:
        """Create a booking for selected hotel"""
        hotel = self.conversation_state['selected_hotel']
        preferences = self.conversation_state['user_preferences']
        
        # Generate unique booking ID
        import random
        import string
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        booking_id = f"HTL{timestamp}{random_suffix}"
        
        # Calculate details
        nights = preferences.get('nights', 1)
        total_amount = hotel['price_per_night'] * nights
        check_in = datetime.now().strftime('%Y-%m-%d')
        
        # Create booking
        booking = {
            'booking_id': booking_id,
            'hotel_name': hotel['name'],
            'hotel_location': hotel['location'],
            'check_in': check_in,
            'check_out': check_in,
            'nights': nights,
            'guests': preferences.get('guests', 1),
            'price_per_night': hotel['price_per_night'],
            'total_amount': total_amount,
            'status': 'confirmed',
            'booking_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.bookings.append(booking)
        
        response = f"🎉 **Booking Confirmed!**\n\n"
        response += f"🏨 {hotel['name']}\n"
        response += f"🆔 Booking ID: {booking_id}\n"
        response += f"📅 {check_in} ({nights} nights)\n"
        response += f"💰 Total: ₹{total_amount}\n"
        response += f"✅ Status: Confirmed\n\n"
        response += "Your booking is confirmed! Have a great stay!"
        
        return {
            'type': 'booking_confirmed',
            'booking': booking,
            'response': response
        }

# Initialize assistant
assistant = SimpleHotelAssistant()

# Streamlit UI
st.set_page_config(
    page_title="AI Hotel Booking Assistant",
    page_icon="🏨",
    layout="wide"
)

st.title("🏨 AI Hotel Booking Assistant")
st.markdown("---")

# Chat interface
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("What would you like to do?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process query
    result = assistant.process_query(prompt)
    
    # Handle hotel selection
    if result['type'] == 'search_results' and result.get('hotels'):
        # Display hotel selection buttons
        for i, hotel in enumerate(result['hotels'], 1):
            if st.button(f"📋 Book Hotel {i}: {hotel['name']}", key=f"book_{i}"):
                assistant.conversation_state['selected_hotel'] = hotel
                assistant.conversation_state['user_preferences']['nights'] = 1
                booking_result = assistant._create_booking()
                
                with st.chat_message("assistant"):
                    st.markdown(booking_result['response'])
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": booking_result['response']
                })
    
    # Display response
    with st.chat_message("assistant"):
        st.markdown(result['response'])
    
    st.session_state.messages.append({
        "role": "assistant", 
        "content": result['response']
    })

# Sidebar with booking history
st.sidebar.title("📋 Booking History")
if assistant.bookings:
    for booking in assistant.bookings[-3:]:  # Show last 3
        st.sidebar.markdown(f"**{booking['hotel_name']}**")
        st.sidebar.markdown(f"ID: {booking['booking_id']}")
        st.sidebar.markdown(f"₹{booking['total_amount']} - {booking['status']}")
        st.sidebar.markdown("---")
else:
    st.sidebar.markdown("No bookings yet")

st.sidebar.markdown("### 💡 Tips")
st.sidebar.markdown("- Try: 'Find hotels in Bangalore under 5000'")
st.sidebar.markdown("- Try: 'Show me hotels in Goa'")
st.sidebar.markdown("- Try: 'Check my booking history'")
