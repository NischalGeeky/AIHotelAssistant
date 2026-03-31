import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date

logger = logging.getLogger(__name__)

class InputValidator:
    """Comprehensive input validation layer"""
    
    def __init__(self):
        self.location_mapping = self._initialize_location_mapping()
        self.amenity_mapping = self._initialize_amenity_mapping()
        self.budget_ranges = self._initialize_budget_ranges()
    
    def _initialize_location_mapping(self) -> Dict[str, str]:
        """Initialize location name normalization mapping"""
        return {
            "bangalore": "Bangalore",
            "bengaluru": "Bangalore",
            "mumbai": "Mumbai",
            "bombay": "Mumbai",
            "delhi": "Delhi",
            "new delhi": "Delhi",
            "goa": "Goa",
            "kerala": "Kerala",
            "manali": "Manali",
            "pune": "Pune",
            "hyderabad": "Hyderabad",
            "chennai": "Chennai",
            "jaipur": "Jaipur",
            "kolkata": "Kolkata",
            "ahmedabad": "Ahmedabad",
            "surat": "Surat",
            "lucknow": "Lucknow",
            "kanpur": "Kanpur",
            "nagpur": "Nagpur"
        }
    
    def _initialize_amenity_mapping(self) -> Dict[str, List[str]]:
        """Initialize amenity keyword mapping"""
        return {
            "wifi": ["wifi", "internet", "wi-fi", "web", "online", "connectivity"],
            "pool": ["pool", "swimming", "swim", "swimming pool", "poolside"],
            "breakfast": ["breakfast", "food", "meal", "dining", "continental", "buffet"],
            "ac": ["ac", "air conditioning", "aircon", "air condition", "cooling"],
            "parking": ["parking", "car", "vehicle", "park", "garage"],
            "gym": ["gym", "fitness", "workout", "exercise", "health", "fitness center"],
            "spa": ["spa", "massage", "wellness", "relaxation", "therapy", "pampering"],
            "restaurant": ["restaurant", "dining", "food", "cuisine", "meal", "eat"],
            "beach_access": ["beach", "beachfront", "sea", "ocean", "sand", "coastal"],
            "mountain_view": ["mountain", "hill", "view", "scenic", "nature", "mountains"]
        }
    
    def _initialize_budget_ranges(self) -> Dict[str, Tuple[int, int]]:
        """Initialize budget range categories"""
        return {
            "budget": (500, 2500),
            "mid_range": (2500, 6000),
            "luxury": (6000, 20000)
        }
    
    def validate_search_input(self, user_input: str) -> Dict[str, Any]:
        """
        Validate and normalize search input
        
        Returns:
            {
                "valid": bool,
                "normalized": str,
                "entities": Dict[str, Any],
                "error": Optional[str]
            }
        """
        try:
            # Basic input validation
            if not user_input or len(user_input.strip()) < 2:
                return {
                    "valid": False,
                    "normalized": "",
                    "entities": {},
                    "error": "Please provide a more detailed search request"
                }
            
            # Extract entities
            entities = self._extract_entities(user_input)
            
            # Validate entities
            validation_result = self._validate_entities(entities)
            
            if not validation_result["valid"]:
                return {
                    "valid": False,
                    "normalized": user_input,
                    "entities": entities,
                    "error": validation_result["error"]
                }
            
            # Normalize input
            normalized_input = self._normalize_input(user_input, entities)
            
            return {
                "valid": True,
                "normalized": normalized_input,
                "entities": entities,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Input validation failed: {str(e)}")
            return {
                "valid": False,
                "normalized": user_input,
                "entities": {},
                "error": "I couldn't process your request. Please try again."
            }
    
    def validate_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize user preferences
        
        Returns:
            Validated and normalized preferences
        """
        validated = preferences.copy()
        
        # Validate and normalize location
        if validated.get("location"):
            location_result = self._validate_location(validated["location"])
            if not location_result["valid"]:
                logger.warning(f"Invalid location: {validated['location']}")
                validated["location"] = None
            else:
                validated["location"] = location_result["normalized"]
        
        # Validate budget
        if validated.get("budget"):
            budget_result = self._validate_budget(validated["budget"])
            if not budget_result["valid"]:
                logger.warning(f"Invalid budget: {validated['budget']}")
                validated["budget"] = None
            else:
                validated["budget"] = budget_result["normalized"]
        
        # Validate guests
        if validated.get("guests"):
            guests_result = self._validate_guests(validated["guests"])
            if not guests_result["valid"]:
                logger.warning(f"Invalid guests: {validated['guests']}")
                validated["guests"] = 1  # Default to 1
            else:
                validated["guests"] = guests_result["normalized"]
        
        # Validate dates
        if validated.get("check_in"):
            check_in_result = self._validate_date(validated["check_in"])
            if not check_in_result["valid"]:
                logger.warning(f"Invalid check-in date: {validated['check_in']}")
                validated["check_in"] = None
            else:
                validated["check_in"] = check_in_result["normalized"]
        
        if validated.get("check_out"):
            check_out_result = self._validate_date(validated["check_out"])
            if not check_out_result["valid"]:
                logger.warning(f"Invalid check-out date: {validated['check_out']}")
                validated["check_out"] = None
            else:
                validated["check_out"] = check_out_result["normalized"]
        
        # Validate nights
        if validated.get("nights"):
            nights_result = self._validate_nights(validated["nights"])
            if not nights_result["valid"]:
                logger.warning(f"Invalid nights: {validated['nights']}")
                validated["nights"] = None
            else:
                validated["nights"] = nights_result["normalized"]
        
        # Validate preferences
        if validated.get("preferences"):
            prefs_result = self._validate_preferences(validated["preferences"])
            validated["preferences"] = prefs_result["normalized"]
        
        return validated
    
    def _extract_entities(self, user_input: str) -> Dict[str, Any]:
        """Extract entities from user input"""
        entities = {}
        user_input_lower = user_input.lower()
        
        # Extract location
        entities["location"] = self._extract_location(user_input_lower)
        
        # Extract budget
        entities["budget"] = self._extract_budget(user_input_lower)
        
        # Extract guests
        entities["guests"] = self._extract_guests(user_input_lower)
        
        # Extract dates
        entities["check_in"], entities["check_out"] = self._extract_dates(user_input_lower)
        
        # Extract nights
        entities["nights"] = self._extract_nights(user_input_lower)
        
        # Extract preferences
        entities["preferences"] = self._extract_preferences(user_input_lower)
        
        return entities
    
    def _extract_location(self, user_input: str) -> Optional[str]:
        """Extract location from user input"""
        for location_key, location_value in self.location_mapping.items():
            if location_key in user_input:
                return location_value
        return None
    
    def _extract_budget(self, user_input: str) -> Optional[int]:
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
                budget = int(next(filter(None, match.groups())))
                # Validate reasonable budget range
                if 500 <= budget <= 50000:
                    return budget
        
        return None
    
    def _extract_guests(self, user_input: str) -> Optional[int]:
        """Extract number of guests from user input"""
        guest_patterns = [
            r'(\d+)\s*guests?',
            r'(\d+)\s*people',
            r'(\d+)\s*person',
            r'for\s*(\d+)\s*people',
            r'for\s*(\d+)\s*guests?'
        ]
        
        for pattern in guest_patterns:
            match = re.search(pattern, user_input)
            if match:
                guests = int(match.group(1))
                # Validate reasonable guest count
                if 1 <= guests <= 20:
                    return guests
        
        # Check for "for me", "for us" patterns
        if "for me" in user_input or "myself" in user_input:
            return 1
        elif "for us" in user_input or "our" in user_input:
            return 2  # Default assumption for "us"
        
        return None
    
    def _extract_dates(self, user_input: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract check-in and check-out dates"""
        check_in = None
        check_out = None
        
        # Try to extract specific dates
        date_patterns = [
            r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})[/\-](\d{1,2})',  # DD/MM (current year)
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, user_input)
            if matches:
                if len(matches) >= 1:
                    check_in = self._parse_date_string(matches[0])
                if len(matches) >= 2:
                    check_out = self._parse_date_string(matches[1])
                break
        
        # Try relative dates
        if "today" in user_input:
            check_in = datetime.now().strftime('%Y-%m-%d')
        elif "tomorrow" in user_input:
            check_in = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        return check_in, check_out
    
    def _extract_nights(self, user_input: str) -> Optional[int]:
        """Extract number of nights from user input"""
        nights_pattern = r'(\d+)\s*(nights?|days?)'
        match = re.search(nights_pattern, user_input)
        
        if match:
            nights = int(match.group(1))
            # Validate reasonable nights count
            if 1 <= nights <= 30:
                return nights
        
        return None
    
    def _extract_preferences(self, user_input: str) -> List[str]:
        """Extract amenity preferences from user input"""
        found_preferences = []
        
        for preference, keywords in self.amenity_mapping.items():
            if any(keyword in user_input for keyword in keywords):
                found_preferences.append(preference)
        
        return found_preferences
    
    def _validate_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted entities"""
        # Check if location is provided (required for search)
        if not entities.get("location"):
            return {
                "valid": False,
                "error": "I need to know which location you're looking for. Please specify a city."
            }
        
        return {"valid": True}
    
    def _validate_location(self, location: str) -> Dict[str, Any]:
        """Validate location"""
        if not location or len(location.strip()) < 2:
            return {"valid": False, "normalized": None}
        
        location_lower = location.lower().strip()
        
        # Check if location is in our mapping
        if location_lower in self.location_mapping:
            return {"valid": True, "normalized": self.location_mapping[location_lower]}
        
        # Check if location contains any of our mapped locations
        for key, value in self.location_mapping.items():
            if key in location_lower:
                return {"valid": True, "normalized": value}
        
        # Return as-is if not found (might be a new location)
        return {"valid": True, "normalized": location.title()}
    
    def _validate_budget(self, budget: Any) -> Dict[str, Any]:
        """Validate budget"""
        try:
            budget_int = int(budget)
            
            # Check reasonable budget range
            if budget_int < 500:
                return {"valid": False, "normalized": None}
            elif budget_int > 50000:
                return {"valid": False, "normalized": None}
            else:
                return {"valid": True, "normalized": budget_int}
        except (ValueError, TypeError):
            return {"valid": False, "normalized": None}
    
    def _validate_guests(self, guests: Any) -> Dict[str, Any]:
        """Validate number of guests"""
        try:
            guests_int = int(guests)
            
            # Check reasonable guest count
            if guests_int < 1 or guests_int > 20:
                return {"valid": False, "normalized": None}
            else:
                return {"valid": True, "normalized": guests_int}
        except (ValueError, TypeError):
            return {"valid": False, "normalized": None}
    
    def _validate_date(self, date_str: str) -> Dict[str, Any]:
        """Validate date string"""
        if not date_str:
            return {"valid": False, "normalized": None}
        
        try:
            # Try to parse the date
            parsed_date = parse_date(date_str)
            
            # Check if date is in the future
            if parsed_date.date() < datetime.now().date():
                return {"valid": False, "normalized": None}
            
            # Check if date is not too far in the future
            if parsed_date.date() > (datetime.now() + timedelta(days=365)).date():
                return {"valid": False, "normalized": None}
            
            return {"valid": True, "normalized": parsed_date.strftime('%Y-%m-%d')}
            
        except Exception:
            return {"valid": False, "normalized": None}
    
    def _validate_nights(self, nights: Any) -> Dict[str, Any]:
        """Validate number of nights"""
        try:
            nights_int = int(nights)
            
            # Check reasonable nights count
            if nights_int < 1 or nights_int > 30:
                return {"valid": False, "normalized": None}
            else:
                return {"valid": True, "normalized": nights_int}
        except (ValueError, TypeError):
            return {"valid": False, "normalized": None}
    
    def _validate_preferences(self, preferences: List[str]) -> Dict[str, Any]:
        """Validate amenity preferences"""
        if not isinstance(preferences, list):
            return {"valid": False, "normalized": []}
        
        # Filter to only valid preferences
        valid_preferences = []
        for pref in preferences:
            if pref in self.amenity_mapping:
                valid_preferences.append(pref)
        
        return {"valid": True, "normalized": valid_preferences}
    
    def _parse_date_string(self, date_tuple: Tuple) -> Optional[str]:
        """Parse date tuple to string"""
        try:
            if len(date_tuple) == 3:
                day, month, year = date_tuple
                parsed_date = datetime(year, month, day)
                return parsed_date.strftime('%Y-%m-%d')
            elif len(date_tuple) == 2:
                day, month = date_tuple
                current_year = datetime.now().year
                parsed_date = datetime(current_year, month, day)
                return parsed_date.strftime('%Y-%m-%d')
        except Exception:
            pass
        
        return None
    
    def _normalize_input(self, user_input: str, entities: Dict[str, Any]) -> str:
        """Normalize user input based on extracted entities"""
        normalized = user_input
        
        # Replace location variations with normalized names
        if entities.get("location"):
            for key, value in self.location_mapping.items():
                normalized = normalized.replace(key, value)
        
        return normalized.strip()
