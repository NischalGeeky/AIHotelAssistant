import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os

class BookingService:
    """Service for hotel booking operations"""
    
    def __init__(self):
        self.bookings = []
        self.booking_file = 'bookings.json'
        self._load_existing_bookings()
    
    def _load_existing_bookings(self):
        """Load existing bookings from file"""
        try:
            if os.path.exists(self.booking_file):
                with open(self.booking_file, 'r', encoding='utf-8') as f:
                    self.bookings = json.load(f)
        except Exception as e:
            print(f"Error loading existing bookings: {e}")
            self.bookings = []
    
    def _save_bookings(self):
        """Save bookings to file"""
        try:
            with open(self.booking_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving bookings: {e}")
    
    def create_booking(self, hotel: Dict[str, Any], user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new booking
        
        Args:
            hotel: Selected hotel dictionary
            user_preferences: User booking preferences
            
        Returns:
            Booking confirmation dictionary
        """
        # Generate booking ID
        booking_id = self._generate_booking_id()
        
        # Calculate dates and costs
        check_in = self._get_check_in_date(user_preferences.get('check_in'))
        check_out = self._get_check_out_date(check_in, user_preferences.get('nights', 1))
        nights = user_preferences.get('nights', 1)
        
        # Calculate total cost
        total_amount = hotel.get('price_per_night', 0) * nights
        
        # Create booking record
        booking = {
            'booking_id': booking_id,
            'hotel_id': hotel.get('id'),
            'hotel_name': hotel.get('name'),
            'hotel_location': hotel.get('location'),
            'check_in': check_in,
            'check_out': check_out,
            'nights': nights,
            'guests': user_preferences.get('guests', 1),
            'price_per_night': hotel.get('price_per_night'),
            'total_amount': total_amount,
            'status': 'confirmed',
            'booking_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'preferences': user_preferences.get('preferences', []),
            'special_requests': user_preferences.get('special_requests', []),
            'contact_info': user_preferences.get('contact_info', {})
        }
        
        # Add to bookings list
        self.bookings.append(booking)
        self._save_bookings()
        
        return booking
    
    def _generate_booking_id(self) -> str:
        """Generate truly unique booking ID"""
        import random
        import string
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"HTL{timestamp}{random_suffix}"
    
    def _get_check_in_date(self, check_in: Optional[str]) -> str:
        """Get check-in date, default to tomorrow"""
        if check_in:
            return check_in
        
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime('%Y-%m-%d')
    
    def _get_check_out_date(self, check_in: str, nights: int) -> str:
        """Calculate check-out date"""
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
            check_out_date = check_in_date + timedelta(days=nights)
            return check_out_date.strftime('%Y-%m-%d')
        except:
            # Fallback to check_in + nights days
            return check_in
    
    def get_booking_by_id(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """Get booking by ID"""
        for booking in self.bookings:
            if booking.get('booking_id') == booking_id:
                return booking
        return None
    
    def get_user_bookings(self, user_email: str = None) -> List[Dict[str, Any]]:
        """Get all bookings for a user (by email if provided)"""
        if user_email:
            user_bookings = []
            for booking in self.bookings:
                if booking.get('contact_info', {}).get('email') == user_email:
                    user_bookings.append(booking)
            return user_bookings
        else:
            return self.bookings.copy()
    
    def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Get all bookings"""
        return self.bookings
    
    def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a booking"""
        for booking in self.bookings:
            if booking.get('booking_id') == booking_id:
                booking['status'] = 'cancelled'
                booking['cancellation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._save_bookings()
                return True
        return False
    
    def modify_booking(self, booking_id: str, modifications: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Modify an existing booking"""
        booking = self.get_booking_by_id(booking_id)
        if not booking:
            return None
        
        # Apply modifications
        allowed_fields = ['guests', 'special_requests', 'preferences']
        for field, value in modifications.items():
            if field in allowed_fields:
                booking[field] = value
        
        booking['last_modified'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._save_bookings()
        
        return booking
    
    def get_booking_summary(self, booking_id: str) -> str:
        """Get formatted booking summary"""
        booking = self.get_booking_by_id(booking_id)
        if not booking:
            return "Booking not found"
        
        summary = f"""
🎉 **Booking Confirmation** ✅

**Booking ID:** {booking['booking_id']}
**Hotel:** {booking['hotel_name']}
**Location:** {booking['hotel_location']}

**Stay Details:**
- Check-in: {booking['check_in']}
- Check-out: {booking['check_out']}
- Nights: {booking['nights']}
- Guests: {booking['guests']}

**Payment:**
- Price per night: ₹{booking['price_per_night']}
- Total amount: ₹{booking['total_amount']}

**Status:** {booking['status'].upper()}
**Booked on:** {booking['booking_date']}

**Contact:** {booking.get('contact_info', {}).get('email', 'N/A')}
        """.strip()
        
        return summary
    
    def calculate_refund(self, booking_id: str) -> Dict[str, Any]:
        """Calculate refund amount for cancelled booking"""
        booking = self.get_booking_by_id(booking_id)
        if not booking or booking.get('status') != 'cancelled':
            return {'refund_amount': 0, 'refund_policy': 'No refund applicable'}
        
        # Simple refund policy (in real system, this would be more complex)
        booking_date = datetime.strptime(booking['booking_date'], '%Y-%m-%d %H:%M:%S')
        cancellation_date = datetime.strptime(booking['cancellation_date'], '%Y-%m-%d %H:%M:%S')
        
        hours_since_booking = (cancellation_date - booking_date).total_seconds() / 3600
        
        if hours_since_booking < 24:
            refund_percent = 100  # Full refund within 24 hours
        elif hours_since_booking < 168:  # Within a week
            refund_percent = 80
        else:
            refund_percent = 50
        
        refund_amount = int(booking['total_amount'] * refund_percent / 100)
        
        return {
            'refund_amount': refund_amount,
            'refund_percent': refund_percent,
            'refund_policy': f'{refund_percent}% refund based on cancellation timing'
        }
    
    def get_booking_statistics(self) -> Dict[str, Any]:
        """Get booking statistics"""
        if not self.bookings:
            return {
                'total_bookings': 0,
                'total_revenue': 0,
                'popular_hotels': [],
                'popular_locations': []
            }
        
        total_bookings = len(self.bookings)
        total_revenue = sum(b['total_amount'] for b in self.bookings if b['status'] == 'confirmed')
        
        # Popular hotels
        hotel_counts = {}
        for booking in self.bookings:
            hotel_name = booking.get('hotel_name', 'Unknown')
            hotel_counts[hotel_name] = hotel_counts.get(hotel_name, 0) + 1
        
        popular_hotels = sorted(hotel_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Popular locations
        location_counts = {}
        for booking in self.bookings:
            location = booking.get('hotel_location', 'Unknown')
            location_counts[location] = location_counts.get(location, 0) + 1
        
        popular_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'popular_hotels': popular_hotels,
            'popular_locations': popular_locations
        }
    
    def search_bookings(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search bookings based on criteria"""
        results = []
        
        for booking in self.bookings:
            match = True
            
            # Search by hotel name
            if 'hotel_name' in criteria:
                if criteria['hotel_name'].lower() not in booking.get('hotel_name', '').lower():
                    match = False
            
            # Search by location
            if 'location' in criteria:
                if criteria['location'].lower() not in booking.get('hotel_location', '').lower():
                    match = False
            
            # Search by status
            if 'status' in criteria:
                if booking.get('status') != criteria['status']:
                    match = False
            
            # Search by date range
            if 'date_from' in criteria:
                booking_date = datetime.strptime(booking['booking_date'], '%Y-%m-%d %H:%M:%S')
                if booking_date < datetime.strptime(criteria['date_from'], '%Y-%m-%d'):
                    match = False
            
            if 'date_to' in criteria:
                booking_date = datetime.strptime(booking['booking_date'], '%Y-%m-%d %H:%M:%S')
                if booking_date > datetime.strptime(criteria['date_to'], '%Y-%m-%d'):
                    match = False
            
            if match:
                results.append(booking)
        
        return results
    
    def generate_booking_report(self, format_type: str = 'summary') -> str:
        """Generate booking report"""
        stats = self.get_booking_statistics()
        
        if format_type == 'summary':
            report = f"""
📊 **Booking Report** - Generated on {datetime.now().strftime('%Y-%m-%d')}

**Summary:**
- Total Bookings: {stats['total_bookings']}
- Total Revenue: ₹{stats['total_revenue']:,.2f}

**Top Hotels:**
{chr(10).join([f"• {hotel}: {count} bookings" for hotel, count in stats['popular_hotels']])}

**Top Locations:**
{chr(10).join([f"• {location}: {count} bookings" for location, count in stats['popular_locations']])}
            """.strip()
        else:
            # Detailed report
            report = "📋 **Detailed Booking Report**\n\n"
            for booking in self.bookings[-10:]:  # Last 10 bookings
                report += f"• {booking['booking_id']}: {booking['hotel_name']} - {booking['status']}\n"
        
        return report
