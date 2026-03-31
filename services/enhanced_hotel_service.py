import json
import os
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

logger = logging.getLogger(__name__)

class EnhancedHotelService:
    """Enhanced hotel service with hybrid semantic search"""
    
    def __init__(self):
        self.hotels = self._load_hotels()
        self.semantic_vectors = None
        self.vectorizer = None
        self._initialize_semantic_search()
    
    def _load_hotels(self) -> List[Dict[str, Any]]:
        """Load hotel data from JSON file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            hotels_file = os.path.join(project_root, 'data', 'hotels.json')
            
            with open(hotels_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading hotels data: {e}")
            return []
    
    def _initialize_semantic_search(self):
        """Initialize semantic search vectors"""
        try:
            # Create enhanced hotel descriptions for semantic matching
            hotel_descriptions = []
            for hotel in self.hotels:
                description = self._create_enhanced_description(hotel)
                hotel_descriptions.append(description)
            
            # Initialize TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                lowercase=True
            )
            
            # Create semantic vectors
            self.semantic_vectors = self.vectorizer.fit_transform(hotel_descriptions)
            logger.info("Semantic search initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing semantic search: {e}")
            self.semantic_vectors = None
            self.vectorizer = None
    
    def _create_enhanced_description(self, hotel: Dict[str, Any]) -> str:
        """Create enhanced description for semantic matching"""
        description_parts = []
        
        # Basic info
        description_parts.append(hotel.get('name', ''))
        description_parts.append(hotel.get('location', ''))
        description_parts.append(hotel.get('description', ''))
        
        # Category
        category = hotel.get('category', '')
        if category == 'luxury':
            description_parts.extend(['luxury', 'premium', 'high-end', 'elegant', 'sophisticated'])
        elif category == 'mid-range':
            description_parts.extend(['comfortable', 'quality', 'value', 'modern'])
        elif category == 'budget':
            description_parts.extend(['affordable', 'economical', 'budget-friendly', 'value'])
        
        # Amenities with semantic keywords
        amenity_keywords = {
            'wifi': ['internet', 'online', 'connectivity', 'business', 'work'],
            'pool': ['swimming', 'recreation', 'leisure', 'fun', 'relaxation'],
            'breakfast': ['food', 'dining', 'meal', 'restaurant', 'cuisine'],
            'ac': ['air conditioning', 'comfort', 'climate', 'cooling'],
            'parking': ['car', 'vehicle', 'convenience', 'access'],
            'gym': ['fitness', 'exercise', 'workout', 'health', 'wellness'],
            'spa': ['massage', 'wellness', 'relaxation', 'pampering', 'therapy'],
            'restaurant': ['dining', 'food', 'cuisine', 'meals', 'restaurant'],
            'beach_access': ['beach', 'ocean', 'sea', 'sand', 'coastal'],
            'mountain_view': ['mountain', 'hill', 'scenic', 'view', 'nature']
        }
        
        for amenity in hotel.get('amenities', []):
            description_parts.append(amenity)
            if amenity in amenity_keywords:
                description_parts.extend(amenity_keywords[amenity])
        
        # Rating-based keywords
        rating = hotel.get('rating', 0)
        if rating >= 4.5:
            description_parts.extend(['excellent', 'outstanding', 'superb', 'top-rated'])
        elif rating >= 4.0:
            description_parts.extend(['very good', 'highly rated', 'popular'])
        elif rating >= 3.5:
            description_parts.extend(['good', 'decent', 'satisfactory'])
        
        # Price-based keywords
        price = hotel.get('price_per_night', 0)
        if price < 2000:
            description_parts.extend(['budget', 'economical', 'affordable'])
        elif price < 5000:
            description_parts.extend(['moderate', 'reasonable', 'fair'])
        else:
            description_parts.extend(['premium', 'luxury', 'high-end'])
        
        return ' '.join(description_parts)
    
    def search_hotels_hybrid(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Hybrid hotel search combining semantic and traditional filtering
        
        Scoring:
        - Semantic match: 40%
        - Rating: 25%
        - Price match: 20%
        - Amenities match: 15%
        """
        if not preferences.get('location'):
            return []
        
        logger.info(f"Starting hybrid search with preferences: {preferences}")
        
        # Step 1: Traditional filtering
        filtered_hotels = self._apply_traditional_filters(preferences)
        
        if not filtered_hotels:
            logger.info("No hotels found after traditional filtering")
            return []
        
        # Step 2: Semantic scoring
        semantic_scores = self._calculate_semantic_scores(preferences, filtered_hotels)
        
        # Step 3: Calculate hybrid scores
        scored_hotels = []
        for i, hotel in enumerate(filtered_hotels):
            hybrid_score = self._calculate_hybrid_score(hotel, preferences, semantic_scores[i])
            scored_hotels.append((hotel, hybrid_score))
        
        # Step 4: Sort by hybrid score
        scored_hotels.sort(key=lambda x: x[1], reverse=True)
        
        # Step 5: Return top results
        results = [hotel for hotel, score in scored_hotels[:5]]
        
        logger.info(f"Hybrid search completed: {len(results)} results found")
        return results
    
    def _apply_traditional_filters(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply traditional filtering based on preferences"""
        filtered = self.hotels.copy()
        
        # Location filter (mandatory)
        location = preferences.get('location', '').lower()
        if location:
            filtered = [h for h in filtered if location in h.get('location', '').lower()]
        
        # Budget filter
        budget = preferences.get('budget')
        if budget:
            filtered = [h for h in filtered if h.get('price_per_night', 0) <= budget]
        
        # Guest filter
        guests = preferences.get('guests', 1)
        if guests > 4:
            filtered = [h for h in filtered if h.get('category') in ['luxury', 'mid-range']]
        
        # Amenities filter
        user_preferences = preferences.get('preferences', [])
        if user_preferences:
            filtered = [h for h in filtered if any(pref in h.get('amenities', []) for pref in user_preferences)]
        
        return filtered
    
    def _calculate_semantic_scores(self, preferences: Dict[str, Any], hotels: List[Dict]) -> List[float]:
        """Calculate semantic similarity scores"""
        if not self.vectorizer or self.semantic_vectors is None:
            return [0.0] * len(hotels)
        
        # Create query vector from user preferences
        query_text = self._create_query_from_preferences(preferences)
        
        try:
            query_vector = self.vectorizer.transform([query_text])
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, self.semantic_vectors)
            
            # Convert to flat list
            return similarities.flatten().tolist()
            
        except Exception as e:
            logger.error(f"Error calculating semantic scores: {e}")
            return [0.0] * len(hotels)
    
    def _create_query_from_preferences(self, preferences: Dict[str, Any]) -> str:
        """Create semantic query from user preferences"""
        query_parts = []
        
        # Location
        if preferences.get('location'):
            query_parts.append(preferences['location'])
        
        # Preferences/amenities
        query_parts.extend(preferences.get('preferences', []))
        
        # Intent-based keywords
        query_lower = ' '.join(query_parts).lower()
        
        # Add semantic keywords based on intent
        if any(word in query_lower for word in ['romantic', 'couple', 'honeymoon']):
            query_parts.extend(['romantic', 'intimate', 'romantic getaway', 'couple'])
        
        if any(word in query_lower for word in ['business', 'work', 'meeting']):
            query_parts.extend(['business', 'professional', 'meeting', 'work'])
        
        if any(word in query_lower for word in ['family', 'kids', 'children']):
            query_parts.extend(['family', 'kid-friendly', 'children', 'family vacation'])
        
        if any(word in query_lower for word in ['luxury', 'premium', 'high-end']):
            query_parts.extend(['luxury', 'premium', 'high-end', 'elegant'])
        
        if any(word in query_lower for word in ['budget', 'cheap', 'affordable']):
            query_parts.extend(['budget', 'affordable', 'economical', 'value'])
        
        return ' '.join(query_parts)
    
    def _calculate_hybrid_score(self, hotel: Dict, preferences: Dict, semantic_score: float) -> float:
        """Calculate hybrid score for a hotel"""
        score = 0.0
        
        # Semantic match (40%)
        score += semantic_score * 0.4
        
        # Rating (25%)
        rating = hotel.get('rating', 0)
        score += (rating / 5.0) * 0.25
        
        # Price match (20%)
        budget = preferences.get('budget')
        if budget:
            price = hotel.get('price_per_night', 0)
            if price <= budget:
                # Better score for better value
                budget_ratio = price / budget
                if budget_ratio <= 0.5:
                    score += 0.2  # Great value
                elif budget_ratio <= 0.8:
                    score += 0.15  # Good value
                else:
                    score += 0.1  # Within budget
        
        # Amenities match (15%)
        user_preferences = preferences.get('preferences', [])
        hotel_amenities = hotel.get('amenities', [])
        
        if user_preferences:
            matching_amenities = set(user_preferences) & set(hotel_amenities)
            amenity_match_ratio = len(matching_amenities) / len(user_preferences)
            score += amenity_match_ratio * 0.15
        
        return score
    
    def get_semantic_explanation(self, hotel: Dict, preferences: Dict, score: float) -> str:
        """Generate explanation for why a hotel was recommended"""
        explanations = []
        
        # Semantic match explanation
        if score > 0.7:
            explanations.append("Excellent match for your preferences")
        elif score > 0.5:
            explanations.append("Good match for your preferences")
        
        # Rating explanation
        rating = hotel.get('rating', 0)
        if rating >= 4.5:
            explanations.append(f"Outstanding rating ({rating}/5)")
        elif rating >= 4.0:
            explanations.append(f"Highly rated ({rating}/5)")
        
        # Price explanation
        budget = preferences.get('budget')
        if budget:
            price = hotel.get('price_per_night', 0)
            if price <= budget * 0.8:
                explanations.append(f"Great value at ₹{price}/night")
            elif price <= budget:
                explanations.append(f"Within budget at ₹{price}/night")
            else:
                explanations.append(f"Slightly above budget at ₹{price}/night")
        
        # Amenities explanation
        user_preferences = preferences.get('preferences', [])
        hotel_amenities = hotel.get('amenities', [])
        matching_amenities = set(user_preferences) & set(hotel_amenities)
        
        if matching_amenities:
            explanations.append(f"Has your preferred amenities: {', '.join(matching_amenities)}")
        
        return " | ".join(explanations)
    
    def get_smart_recommendations(self, preferences: Dict, current_results: List[Dict]) -> Dict[str, Any]:
        """Get smart recommendations based on search context"""
        recommendations = {
            "nearby_cities": [],
            "similar_hotels": [],
            "price_alternatives": [],
            "amenity_alternatives": []
        }
        
        if not current_results:
            return recommendations
        
        # Nearby cities
        location = preferences.get('location')
        if location:
            recommendations["nearby_cities"] = self._get_nearby_cities(location)
        
        # Similar hotels
        if current_results:
            top_hotel = current_results[0]
            recommendations["similar_hotels"] = self._get_similar_hotels(top_hotel, exclude_current=current_results)
        
        # Price alternatives
        budget = preferences.get('budget')
        if budget and current_results:
            recommendations["price_alternatives"] = self._get_price_alternatives(budget, preferences)
        
        # Amenity alternatives
        user_preferences = preferences.get('preferences', [])
        if user_preferences:
            recommendations["amenity_alternatives"] = self._get_amenity_alternatives(user_preferences, preferences)
        
        return recommendations
    
    def _get_nearby_cities(self, location: str) -> List[str]:
        """Get nearby cities for recommendations"""
        nearby_mapping = {
            "Bangalore": ["Mysore", "Hosur", "Tumkur"],
            "Mumbai": ["Pune", "Navi Mumbai", "Thane"],
            "Delhi": ["Gurgaon", "Noida", "Faridabad"],
            "Goa": ["Panjim", "Margao", "Vasco"],
            "Chennai": ["Coimbatore", "Bangalore", "Pondicherry"],
            "Hyderabad": ["Secunderabad", "Warangal", "Nizamabad"],
            "Pune": ["Mumbai", "Lonavala", "Khandala"],
            "Kerala": ["Kochi", "Munnar", "Thekkady"]
        }
        
        return nearby_mapping.get(location, [])
    
    def _get_similar_hotels(self, hotel: Dict, exclude_current: List[Dict]) -> List[Dict]:
        """Get hotels similar to the given hotel"""
        similar_hotels = []
        
        # Find hotels in same location
        location_hotels = [h for h in self.hotels if h.get('location') == hotel.get('location')]
        
        # Exclude current results
        exclude_ids = {h.get('id') for h in exclude_current}
        location_hotels = [h for h in location_hotels if h.get('id') not in exclude_ids]
        
        # Sort by rating similarity and price proximity
        current_rating = hotel.get('rating', 0)
        current_price = hotel.get('price_per_night', 0)
        
        scored_hotels = []
        for h in location_hotels:
            rating_diff = abs(h.get('rating', 0) - current_rating)
            price_diff = abs(h.get('price_per_night', 0) - current_price) / current_price if current_price > 0 else 1
            
            similarity_score = 1 - (rating_diff + price_diff) / 2
            scored_hotels.append((h, similarity_score))
        
        # Sort by similarity score
        scored_hotels.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 3 similar hotels
        return [hotel for hotel, score in scored_hotels[:3]]
    
    def _get_price_alternatives(self, budget: int, preferences: Dict) -> List[Dict]:
        """Get hotels at different price points"""
        alternatives = {"budget": [], "mid_range": [], "luxury": []}
        
        # Define price ranges
        budget_range = (500, budget * 0.7)
        mid_range = (budget * 0.7, budget * 1.3)
        luxury_range = (budget * 1.3, budget * 2)
        
        for hotel in self.hotels:
            price = hotel.get('price_per_night', 0)
            
            if budget_range[0] <= price <= budget_range[1]:
                alternatives["budget"].append(hotel)
            elif mid_range[0] <= price <= mid_range[1]:
                alternatives["mid_range"].append(hotel)
            elif luxury_range[0] <= price <= luxury_range[1]:
                alternatives["luxury"].append(hotel)
        
        # Return top 2 from each category
        result = []
        for category in ["budget", "mid_range", "luxury"]:
            hotels = sorted(alternatives[category], key=lambda x: x.get('rating', 0), reverse=True)
            result.extend(hotels[:2])
        
        return result[:4]  # Return up to 4 alternatives
    
    def _get_amenity_alternatives(self, preferences: List[str], search_preferences: Dict) -> List[Dict]:
        """Get hotels with alternative amenities"""
        alternative_amenities = {
            "wifi": ["parking", "breakfast"],
            "pool": ["spa", "gym"],
            "breakfast": ["restaurant", "wifi"],
            "ac": ["wifi", "parking"],
            "parking": ["wifi", "ac"],
            "gym": ["pool", "spa"],
            "spa": ["pool", "gym"]
        }
        
        # Find alternative amenities
        alternatives = set()
        for pref in preferences:
            if pref in alternative_amenities:
                alternatives.update(alternative_amenities[pref])
        
        if not alternatives:
            return []
        
        # Search for hotels with alternative amenities
        alt_preferences = search_preferences.copy()
        alt_preferences["preferences"] = list(alternatives)
        
        return self.search_hotels_hybrid(alt_preferences)[:3]
