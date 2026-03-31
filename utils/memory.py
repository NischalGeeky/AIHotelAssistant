import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationIntent(Enum):
    SEARCH = "search"
    REFINE = "refine"
    BOOK = "book"
    CONFIRMATION = "confirmation"
    HELP = "help"
    UNKNOWN = "unknown"

@dataclass
class ConversationState:
    """Structured conversation state for intelligent context management"""
    intent: ConversationIntent = ConversationIntent.UNKNOWN
    filters: Dict[str, Any] = None
    last_results: List[Dict[str, Any]] = None
    selected_hotel: Optional[Dict[str, Any]] = None
    missing_fields: List[str] = None
    conversation_history: List[Dict[str, Any]] = None
    user_profile: Dict[str, Any] = None
    last_updated: str = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if self.last_results is None:
            self.last_results = []
        if self.missing_fields is None:
            self.missing_fields = []
        if self.conversation_history is None:
            self.conversation_history = []
        if self.user_profile is None:
            self.user_profile = {}
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()

class ConversationMemory:
    """Advanced context-aware memory system for intelligent conversations"""
    
    def __init__(self):
        self.state = ConversationState()
        self.intent_patterns = self._initialize_intent_patterns()
        self.required_fields = {
            ConversationIntent.SEARCH: ["location"],
            ConversationIntent.BOOK: ["location", "dates", "guests"],
            ConversationIntent.REFINE: []
        }
    
    def _initialize_intent_patterns(self) -> Dict[ConversationIntent, List[str]]:
        """Initialize intent detection patterns"""
        return {
            ConversationIntent.SEARCH: [
                "find", "search", "looking for", "need", "want", "show me", 
                "get me", "hotel", "stay", "accommodation", "available", "options",
                "what hotels", "where can i", "suggest", "recommend"
            ],
            ConversationIntent.REFINE: [
                "cheaper", "expensive", "only", "with", "without", "prefer",
                "filter", "narrow", "something", "else", "different", "more",
                "less", "better", "closer", "near"
            ],
            ConversationIntent.BOOK: [
                "book", "reserve", "confirm", "booking", "reserve", "take it",
                "i'll take", "want to book", "book this", "book the", "reserve this"
            ],
            ConversationIntent.CONFIRMATION: [
                "yes", "confirm", "sure", "ok", "proceed", "definitely",
                "sounds good", "perfect", "that's fine", "go ahead"
            ],
            ConversationIntent.HELP: [
                "help", "how", "what", "assist", "guide", "explain",
                "support", "instructions", "tutorial"
            ]
        }
    
    def detect_intent(self, user_input: str) -> ConversationIntent:
        """Detect user intent with confidence scoring"""
        user_input_lower = user_input.lower()
        intent_scores = {}
        
        # Special patterns to avoid false positives
        booking_false_positives = ["history", "status", "details", "information", "check", "view"]
        search_false_positives = ["ticket", "flight", "train", "bus"]
        
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in user_input_lower)
            
            # Reduce score for false positives
            if intent == ConversationIntent.BOOK:
                for false_positive in booking_false_positives:
                    if false_positive in user_input_lower:
                        score -= 1
            
            if intent == ConversationIntent.SEARCH:
                for false_positive in search_false_positives:
                    if false_positive in user_input_lower:
                        score -= 1
            
            intent_scores[intent] = max(0, score)  # Don't allow negative scores
        
        # Get intent with highest score
        if not any(intent_scores.values()):
            return ConversationIntent.UNKNOWN
        
        best_intent = max(intent_scores, key=intent_scores.get)
        
        # Additional context checks
        if best_intent == ConversationIntent.BOOK:
            # Make sure it's actually about booking, not checking status
            if any(word in user_input_lower for word in ["history", "status", "details", "check", "view"]):
                return ConversationIntent.HELP
        
        # Check for booking history/status requests
        if any(word in user_input_lower for word in ["history", "status", "details", "check", "view", "my booking", "booking history"]):
            if any(word in user_input_lower for word in ["booking", "reservation"]):
                return ConversationIntent.HELP
        
        # Context-aware intent adjustment
        if self.state.intent == ConversationIntent.SEARCH and best_intent == ConversationIntent.UNKNOWN:
            # If we're in search context and input is unclear, assume refinement
            if any(word in user_input_lower for word in ["cheaper", "better", "different"]):
                return ConversationIntent.REFINE
        
        return best_intent if intent_scores[best_intent] > 0 else ConversationIntent.UNKNOWN
    
    def update_state(self, user_input: str, response: str, new_filters: Dict[str, Any] = None):
        """Update conversation state with new information"""
        # Detect intent
        new_intent = self.detect_intent(user_input)
        
        # Update conversation history
        self.state.conversation_history.append({
            "user_input": user_input,
            "assistant_response": response,
            "intent": new_intent.value,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 10 exchanges
        if len(self.state.conversation_history) > 10:
            self.state.conversation_history = self.state.conversation_history[-10:]
        
        # Update intent
        if new_intent != ConversationIntent.UNKNOWN:
            self.state.intent = new_intent
        
        # Update filters
        if new_filters:
            self.state.filters.update(new_filters)
        
        # Update timestamp
        self.state.last_updated = datetime.now().isoformat()
        
        logger.info(f"Conversation state updated - Intent: {new_intent.value}, Filters: {self.state.filters}")
    
    def identify_missing_fields(self, intent: ConversationIntent) -> List[str]:
        """Identify required fields that are missing for the current intent"""
        required = self.required_fields.get(intent, [])
        missing = []
        
        for field in required:
            if field == "location" and not self.state.filters.get("location"):
                missing.append("location")
            elif field == "dates" and not (self.state.filters.get("check_in") or self.state.filters.get("nights")):
                missing.append("dates")
            elif field == "guests" and not self.state.filters.get("guests"):
                missing.append("guests")
        
        self.state.missing_fields = missing
        return missing
    
    def should_ask_follow_up(self, user_input: str) -> bool:
        """Determine if follow-up questions are needed"""
        intent = self.detect_intent(user_input)
        missing_fields = self.identify_missing_fields(intent)
        
        # Don't ask for missing fields if user is refining
        if intent == ConversationIntent.REFINE:
            return False
        
        # Don't ask if we already asked recently
        if missing_fields:
            # Check if we asked about these fields in the last 2 exchanges
            recent_exchanges = self.state.conversation_history[-2:]
            for field in missing_fields:
                for exchange in recent_exchanges:
                    if field in exchange.get("assistant_response", "").lower():
                        return False
            return True
        
        return False
    
    def generate_follow_up_questions(self, user_input: str) -> str:
        """Generate intelligent follow-up questions"""
        intent = self.detect_intent(user_input)
        missing_fields = self.identify_missing_fields(intent)
        
        if not missing_fields:
            return ""
        
        questions = []
        
        if "location" in missing_fields:
            questions.append("Which city or location are you looking for?")
        
        if "dates" in missing_fields:
            nights = self.state.filters.get("nights")
            if nights:
                questions.append(f"What dates would you like to stay for {nights} nights?")
            else:
                questions.append("What dates and how many nights are you planning to stay?")
        
        if "guests" in missing_fields:
            questions.append("How many guests will be staying?")
        
        if len(questions) == 1:
            return questions[0]
        elif len(questions) == 2:
            return f"{questions[0]} And {questions[1].lower()}"
        else:
            return "I need a few more details: " + ", ".join(questions[:-1]) + f", and {questions[-1].lower()}"
    
    def detect_refinement_intent(self, user_input: str) -> Dict[str, Any]:
        """Detect what user is trying to refine"""
        user_input_lower = user_input.lower()
        refinements = {}
        
        # Budget refinement
        if any(word in user_input_lower for word in ["cheaper", "budget", "under", "less"]):
            current_budget = self.state.filters.get("budget")
            if current_budget:
                refinements["budget"] = int(current_budget * 0.8)  # 20% cheaper
            else:
                refinements["budget"] = 3000  # Default budget
        
        # Amenities refinement
        amenity_keywords = {
            "pool": ["pool", "swimming"],
            "wifi": ["wifi", "internet"],
            "breakfast": ["breakfast", "food"],
            "ac": ["ac", "air conditioning"],
            "parking": ["parking", "car"],
            "gym": ["gym", "fitness"],
            "spa": ["spa", "massage"]
        }
        
        for amenity, keywords in amenity_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                current_prefs = self.state.filters.get("preferences", [])
                if amenity not in current_prefs:
                    refinements["preferences"] = current_prefs + [amenity]
        
        # Location refinement
        if "nearby" in user_input_lower or "close" in user_input_lower:
            current_location = self.state.filters.get("location")
            if current_location:
                refinements["location"] = current_location  # Keep same location
        
        return refinements
    
    def get_context_summary(self) -> str:
        """Get a summary of current conversation context"""
        context_parts = []
        
        if self.state.filters.get("location"):
            context_parts.append(f"Location: {self.state.filters['location']}")
        
        if self.state.filters.get("budget"):
            context_parts.append(f"Budget: ₹{self.state.filters['budget']}")
        
        if self.state.filters.get("guests"):
            context_parts.append(f"Guests: {self.state.filters['guests']}")
        
        if self.state.filters.get("nights"):
            context_parts.append(f"Nights: {self.state.filters['nights']}")
        
        if self.state.filters.get("preferences"):
            context_parts.append(f"Preferences: {', '.join(self.state.filters['preferences'])}")
        
        if self.state.last_results:
            context_parts.append(f"Last search: {len(self.state.last_results)} hotels found")
        
        return " | ".join(context_parts) if context_parts else "No context yet"
    
    def reset_context(self):
        """Reset conversation context for new booking"""
        self.state = ConversationState()
        logger.info("Conversation context reset")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for persistence"""
        return asdict(self.state)
    
    def from_dict(self, data: Dict[str, Any]):
        """Load state from dictionary"""
        self.state = ConversationState(**data)
        logger.info("Conversation state loaded from dictionary")
