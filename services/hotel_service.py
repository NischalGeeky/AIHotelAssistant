import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class HotelService:
    """Service for hotel search and filtering operations"""
    
    def __init__(self):
        self.hotels = self._load_hotels()
    
    def _load_hotels(self) -> List[Dict[str, Any]]:
        """Load hotel data from JSON file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            hotels_file = os.path.join(project_root, 'data', 'hotels.json')
            
            with open(hotels_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading hotels data: {e}")
            return []
    
    def search_hotels(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search hotels based on user preferences
        
        Args:
            preferences: Dictionary containing search criteria
                - location: str (required)
                - budget: int (optional)
                - guests: int (optional)
                - preferences: List[str] (optional)
                - check_in: str (optional)
                - check_out: str (optional)
                - nights: int (optional)
        
        Returns:
            List of matching hotels, sorted by relevance
        """
        if not preferences.get('location'):
            return []
        
        # Start with all hotels
        filtered_hotels = self.hotels.copy()
        
        # Apply filters
        filtered_hotels = self._filter_by_location(filtered_hotels, preferences['location'])
        filtered_hotels = self._filter_by_budget(filtered_hotels, preferences.get('budget'))
        filtered_hotels = self._filter_by_preferences(filtered_hotels, preferences.get('preferences', []))
        filtered_hotels = self._filter_by_guests(filtered_hotels, preferences.get('guests', 1))
        
        # Sort and rank results
        ranked_hotels = self._rank_hotels(filtered_hotels, preferences)
        
        # Return top 5 results
        return ranked_hotels[:5]
    
    def _filter_by_location(self, hotels: List[Dict[str, Any]], location: str) -> List[Dict[str, Any]]:
        """Filter hotels by location"""
        if not location:
            return hotels
        
        location_lower = location.lower()
        filtered = []
        
        for hotel in hotels:
            hotel_location = hotel.get('location', '').lower()
            if location_lower in hotel_location or hotel_location in location_lower:
                filtered.append(hotel)
        
        return filtered
    
    def _filter_by_budget(self, hotels: List[Dict[str, Any]], budget: Optional[int]) -> List[Dict[str, Any]]:
        """Filter hotels by budget"""
        if not budget:
            return hotels
        
        filtered = []
        for hotel in hotels:
            price = hotel.get('price_per_night', 0)
            if price <= budget:
                filtered.append(hotel)
        
        return filtered
    
    def _filter_by_preferences(self, hotels: List[Dict[str, Any]], preferences: List[str]) -> List[Dict[str, Any]]:
        """Filter hotels by amenities/preferences"""
        if not preferences:
            return hotels
        
        filtered = []
        for hotel in hotels:
            hotel_amenities = [amenity.lower() for amenity in hotel.get('amenities', [])]
            user_preferences = [pref.lower() for pref in preferences]
            
            # Check if hotel has at least one requested preference
            if any(pref in hotel_amenities for pref in user_preferences):
                filtered.append(hotel)
            elif not preferences:  # If no specific preferences, include all
                filtered.append(hotel)
        
        return filtered
    
    def _filter_by_guests(self, hotels: List[Dict[str, Any]], guests: int) -> List[Dict[str, Any]]:
        """Filter hotels suitable for number of guests"""
        # For simplicity, we'll assume all hotels can accommodate up to 4 guests
        # In a real system, this would check hotel capacity
        if guests <= 4:
            return hotels
        else:
            # Return hotels that can accommodate larger groups
            return [hotel for hotel in hotels if hotel.get('category') in ['luxury', 'mid-range']]
    
    def _rank_hotels(self, hotels: List[Dict[str, Any]], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank hotels by relevance to user preferences"""
        if not hotels:
            return []
        
        # Calculate relevance score for each hotel
        scored_hotels = []
        for hotel in hotels:
            score = self._calculate_relevance_score(hotel, preferences)
            scored_hotels.append((hotel, score))
        
        # Sort by score (descending)
        scored_hotels.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the hotels (sorted)
        return [hotel for hotel, score in scored_hotels]
    
    def _calculate_relevance_score(self, hotel: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """Calculate relevance score for a hotel based on preferences"""
        score = 0.0
        
        # Base score from rating (0-10 points)
        rating = hotel.get('rating', 0)
        score += rating * 2
        
        # Budget match bonus (up to 5 points)
        budget = preferences.get('budget')
        if budget:
            price = hotel.get('price_per_night', 0)
            if price <= budget:
                # Higher bonus for better value
                budget_ratio = price / budget
                if budget_ratio <= 0.5:
                    score += 5  # Great value
                elif budget_ratio <= 0.8:
                    score += 3  # Good value
                else:
                    score += 1  # Within budget
        
        # Amenities match bonus (up to 5 points)
        user_preferences = [pref.lower() for pref in preferences.get('preferences', [])]
        hotel_amenities = [amenity.lower() for amenity in hotel.get('amenities', [])]
        
        matching_amenities = set(user_preferences) & set(hotel_amenities)
        if user_preferences:
            amenity_match_ratio = len(matching_amenities) / len(user_preferences)
            score += amenity_match_ratio * 5
        
        # Category preference bonus (up to 3 points)
        # Assume users prefer mid-range unless they specify high budget
        if budget and budget > 5000:
            if hotel.get('category') == 'luxury':
                score += 3
            elif hotel.get('category') == 'mid-range':
                score += 1
        else:
            if hotel.get('category') == 'mid-range':
                score += 2
            elif hotel.get('category') == 'budget':
                score += 1
        
        return score
    
    def get_hotel_by_id(self, hotel_id: int) -> Optional[Dict[str, Any]]:
        """Get hotel by ID"""
        for hotel in self.hotels:
            if hotel.get('id') == hotel_id:
                return hotel
        return None
    
    def get_hotels_by_location(self, location: str) -> List[Dict[str, Any]]:
        """Get all hotels in a specific location"""
        return self._filter_by_location(self.hotels, location)
    
    def get_hotel_suggestions(self, partial_location: str) -> List[str]:
        """Get location suggestions based on partial input"""
        locations = set()
        partial_lower = partial_location.lower()
        
        for hotel in self.hotels:
            location = hotel.get('location', '')
            if partial_lower in location.lower():
                locations.add(location)
        
        return sorted(list(locations))
    
    def calculate_total_cost(self, hotel: Dict[str, Any], nights: int) -> int:
        """Calculate total cost for a stay"""
        price_per_night = hotel.get('price_per_night', 0)
        return price_per_night * nights
    
    def get_similar_hotels(self, hotel: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
        """Get hotels similar to the given hotel"""
        similar_hotels = []
        
        # Find hotels in same location
        location_hotels = self._filter_by_location(self.hotels, hotel.get('location', ''))
        
        # Exclude the current hotel
        location_hotels = [h for h in location_hotels if h.get('id') != hotel.get('id')]
        
        # Sort by rating similarity and price proximity
        current_rating = hotel.get('rating', 0)
        current_price = hotel.get('price_per_night', 0)
        
        scored_hotels = []
        for h in location_hotels:
            rating_diff = abs(h.get('rating', 0) - current_rating)
            price_diff = abs(h.get('price_per_night', 0) - current_price) / current_price if current_price > 0 else 1
            
            # Lower score means more similar
            similarity_score = rating_diff + price_diff
            scored_hotels.append((h, similarity_score))
        
        # Sort by similarity score (ascending)
        scored_hotels.sort(key=lambda x: x[1])
        
        # Return top similar hotels
        return [hotel for hotel, score in scored_hotels[:limit]]
    
    def get_popular_destinations(self) -> List[Dict[str, Any]]:
        """Get popular destinations with hotel counts"""
        destination_counts = {}
        
        for hotel in self.hotels:
            location = hotel.get('location', '')
            if location not in destination_counts:
                destination_counts[location] = {
                    'location': location,
                    'count': 0,
                    'avg_price': 0,
                    'avg_rating': 0
                }
            
            dest = destination_counts[location]
            dest['count'] += 1
            dest['avg_price'] += hotel.get('price_per_night', 0)
            dest['avg_rating'] += hotel.get('rating', 0)
        
        # Calculate averages
        for dest in destination_counts.values():
            if dest['count'] > 0:
                dest['avg_price'] = dest['avg_price'] // dest['count']
                dest['avg_rating'] = round(dest['avg_rating'] / dest['count'], 1)
        
        # Sort by hotel count and return
        popular_destinations = sorted(destination_counts.values(), 
                                   key=lambda x: x['count'], reverse=True)
        
        return popular_destinations[:10]  # Top 10 destinations
    
    def search_by_amenity(self, amenity: str) -> List[Dict[str, Any]]:
        """Search hotels that have a specific amenity"""
        amenity_lower = amenity.lower()
        matching_hotels = []
        
        for hotel in self.hotels:
            amenities = [a.lower() for a in hotel.get('amenities', [])]
            if amenity_lower in amenities:
                matching_hotels.append(hotel)
        
        return self._rank_hotels(matching_hotels, {})
    
    def get_price_ranges(self, location: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get hotels grouped by price ranges"""
        hotels = self.hotels
        if location:
            hotels = self._filter_by_location(hotels, location)
        
        price_ranges = {
            'budget': [],      # Under 3000
            'mid-range': [],   # 3000-6000
            'luxury': []       # Over 6000
        }
        
        for hotel in hotels:
            price = hotel.get('price_per_night', 0)
            if price < 3000:
                price_ranges['budget'].append(hotel)
            elif price <= 6000:
                price_ranges['mid-range'].append(hotel)
            else:
                price_ranges['luxury'].append(hotel)
        
        # Sort each range by rating
        for range_name in price_ranges:
            price_ranges[range_name] = sorted(price_ranges[range_name], 
                                            key=lambda x: x.get('rating', 0), reverse=True)
        
        return price_ranges
