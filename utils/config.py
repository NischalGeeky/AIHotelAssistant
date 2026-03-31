import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """LLM Configuration"""
    api_key: str
    model_name: str
    temperature: float
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        return cls(
            api_key=os.getenv("GROQ_API_KEY", "gsk_your_api_key_here"),
            model_name=os.getenv("GROQ_MODEL_NAME", "llama3-70b-8192"),
            temperature=float(os.getenv("GROQ_TEMPERATURE", "0.1"))
        )

@dataclass
class AppConfig:
    """Application Configuration"""
    name: str
    version: str
    debug: bool
    log_level: str
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        return cls(
            name=os.getenv("APP_NAME", "AI Hotel Booking Assistant"),
            version=os.getenv("APP_VERSION", "2.0.0"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )

@dataclass
class DatabaseConfig:
    """Database Configuration"""
    url: str
    hotels_data_path: str
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        return cls(
            url=os.getenv("DATABASE_URL", "sqlite:///bookings.db"),
            hotels_data_path=os.getenv("HOTELS_DATA_PATH", "data/hotels.json")
        )

@dataclass
class UIConfig:
    """UI Configuration"""
    theme_color_primary: str
    theme_color_secondary: str
    max_hotels_displayed: int
    chat_history_limit: int
    
    @classmethod
    def from_env(cls) -> 'UIConfig':
        return cls(
            theme_color_primary=os.getenv("THEME_COLOR_PRIMARY", "#667eea"),
            theme_color_secondary=os.getenv("THEME_COLOR_SECONDARY", "#764ba2"),
            max_hotels_displayed=int(os.getenv("MAX_HOTELS_DISPLAYED", "5")),
            chat_history_limit=int(os.getenv("CHAT_HISTORY_LIMIT", "10"))
        )

@dataclass
class SemanticConfig:
    """Semantic Search Configuration"""
    enabled: bool
    vector_max_features: int
    semantic_weight: float
    rating_weight: float
    price_weight: float
    amenities_weight: float
    
    @classmethod
    def from_env(cls) -> 'SemanticConfig':
        return cls(
            enabled=os.getenv("SEMANTIC_SEARCH_ENABLED", "true").lower() == "true",
            vector_max_features=int(os.getenv("VECTOR_MAX_FEATURES", "1000")),
            semantic_weight=float(os.getenv("SEMANTIC_WEIGHT", "0.4")),
            rating_weight=float(os.getenv("RATING_WEIGHT", "0.25")),
            price_weight=float(os.getenv("PRICE_WEIGHT", "0.2")),
            amenities_weight=float(os.getenv("AMENITIES_WEIGHT", "0.15"))
        )

@dataclass
class ValidationConfig:
    """Validation Configuration"""
    min_budget: int
    max_budget: int
    min_guests: int
    max_guests: int
    min_nights: int
    max_nights: int
    
    @classmethod
    def from_env(cls) -> 'ValidationConfig':
        return cls(
            min_budget=int(os.getenv("MIN_BUDGET", "500")),
            max_budget=int(os.getenv("MAX_BUDGET", "50000")),
            min_guests=int(os.getenv("MIN_GUESTS", "1")),
            max_guests=int(os.getenv("MAX_GUESTS", "20")),
            min_nights=int(os.getenv("MIN_NIGHTS", "1")),
            max_nights=int(os.getenv("MAX_NIGHTS", "30"))
        )

@dataclass
class PerformanceConfig:
    """Performance Configuration"""
    cache_enabled: bool
    cache_ttl: int
    rate_limit_enabled: bool
    rate_limit_requests: int
    rate_limit_window: int
    
    @classmethod
    def from_env(cls) -> 'PerformanceConfig':
        return cls(
            cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
        )

@dataclass
class SecurityConfig:
    """Security Configuration"""
    session_timeout: int
    cors_enabled: bool
    allowed_origins: list
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
        allowed_origins = [origin.strip() for origin in origins_str.split(",")]
        
        return cls(
            session_timeout=int(os.getenv("SESSION_TIMEOUT", "1800")),
            cors_enabled=os.getenv("CORS_ENABLED", "true").lower() == "true",
            allowed_origins=allowed_origins
        )

@dataclass
class MonitoringConfig:
    """Monitoring Configuration"""
    enabled: bool
    metrics_endpoint: str
    health_check_endpoint: str
    
    @classmethod
    def from_env(cls) -> 'MonitoringConfig':
        return cls(
            enabled=os.getenv("MONITORING_ENABLED", "true").lower() == "true",
            metrics_endpoint=os.getenv("METRICS_ENDPOINT", "/metrics"),
            health_check_endpoint=os.getenv("HEALTH_CHECK_ENDPOINT", "/health")
        )

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.llm = LLMConfig.from_env()
        self.app = AppConfig.from_env()
        self.database = DatabaseConfig.from_env()
        self.ui = UIConfig.from_env()
        self.semantic = SemanticConfig.from_env()
        self.validation = ValidationConfig.from_env()
        self.performance = PerformanceConfig.from_env()
        self.security = SecurityConfig.from_env()
        self.monitoring = MonitoringConfig.from_env()
        
        # Validate configuration
        self._validate_config()
        
        # Setup logging
        self._setup_logging()
    
    def _validate_config(self):
        """Validate configuration values"""
        errors = []
        
        # Validate LLM config
        if not self.llm.api_key or self.llm.api_key == "gsk_your_api_key_here":
            errors.append("GROQ_API_KEY is not set or using default value")
        
        # Validate budget range
        if self.validation.min_budget >= self.validation.max_budget:
            errors.append("MIN_BUDGET must be less than MAX_BUDGET")
        
        # Validate guest range
        if self.validation.min_guests >= self.validation.max_guests:
            errors.append("MIN_GUESTS must be less than MAX_GUESTS")
        
        # Validate semantic weights
        total_weight = (self.semantic.semantic_weight + self.semantic.rating_weight + 
                        self.semantic.price_weight + self.semantic.amenities_weight)
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"Semantic weights must sum to 1.0, current sum: {total_weight}")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"• {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def _setup_logging(self):
        """Setup logging based on configuration"""
        log_level = getattr(logging, self.app.log_level.upper(), logging.INFO)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('hotel_booking_assistant.log')
            ]
        )
        
        logger.info(f"Logging configured with level: {self.app.log_level}")
    
    def get_database_url(self) -> str:
        """Get database URL"""
        return self.database.url
    
    def get_hotels_data_path(self) -> str:
        """Get hotels data file path"""
        return self.database.hotels_data_path
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.app.debug
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.app.debug
    
    def get_cors_origins(self) -> list:
        """Get CORS allowed origins"""
        return self.security.allowed_origins if self.security.cors_enabled else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "llm": {
                "model_name": self.llm.model_name,
                "temperature": self.llm.temperature
            },
            "app": {
                "name": self.app.name,
                "version": self.app.version,
                "debug": self.app.debug
            },
            "ui": {
                "max_hotels_displayed": self.ui.max_hotels_displayed,
                "chat_history_limit": self.ui.chat_history_limit
            },
            "semantic": {
                "enabled": self.semantic.enabled,
                "weights": {
                    "semantic": self.semantic.semantic_weight,
                    "rating": self.semantic.rating_weight,
                    "price": self.semantic.price_weight,
                    "amenities": self.semantic.amenities_weight
                }
            },
            "validation": {
                "budget_range": (self.validation.min_budget, self.validation.max_budget),
                "guests_range": (self.validation.min_guests, self.validation.max_guests),
                "nights_range": (self.validation.min_nights, self.validation.max_nights)
            }
        }

# Global configuration instance
config = Config()

def get_config() -> Config:
    """Get global configuration instance"""
    return config

def reload_config():
    """Reload configuration from environment"""
    global config
    config = Config()
    logger.info("Configuration reloaded")
