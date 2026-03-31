import logging
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime

# Import services
from services.enhanced_hotel_service import EnhancedHotelService
from services.booking_service import BookingService
from utils.intelligence import ConversationIntelligence
from utils.validation import InputValidator
from utils.monitoring import get_monitoring_service, track_performance
from utils.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Hotel Booking Assistant API",
    description="Production-grade hotel booking assistant with intelligent search and booking capabilities",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Get configuration
config = get_config()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize services
hotel_service = EnhancedHotelService()
booking_service = BookingService()
conversation_intelligence = ConversationIntelligence(hotel_service)
input_validator = InputValidator()
monitoring_service = get_monitoring_service()

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str
    preferences: Optional[Dict[str, Any]] = None

class BookingRequest(BaseModel):
    hotel_id: str
    preferences: Dict[str, Any]

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

# Health check endpoint
@app.get("/health")
@track_performance("health_check")
async def health_check():
    """Health check endpoint"""
    health_status = monitoring_service.get_health_status()
    return JSONResponse(
        content=health_status,
        status_code=200 if health_status["status"] == "healthy" else 503
    )

# Metrics endpoint
@app.get("/metrics")
@track_performance("metrics")
async def get_metrics():
    """Get system metrics"""
    metrics = monitoring_service.get_metrics_summary()
    return JSONResponse(content=metrics)

# Search hotels endpoint
@app.post("/search")
@track_performance("search")
async def search_hotels(request: SearchRequest):
    """Search for hotels based on query and preferences"""
    try:
        # Process with conversation intelligence
        result = conversation_intelligence.process_user_input(request.query)
        
        if result["response_type"] == "search_results":
            return JSONResponse(content={
                "success": True,
                "hotels": result.get("hotels", []),
                "intent": result["intent"].value,
                "response": result["response"]
            })
        else:
            return JSONResponse(content={
                "success": False,
                "message": result["response"],
                "intent": result["intent"].value
            })
            
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

# Book hotel endpoint
@app.post("/book")
@track_performance("booking")
async def book_hotel(request: BookingRequest):
    """Book a hotel"""
    try:
        # Validate input
        validation_result = input_validator.validate_booking_preferences(request.preferences)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid input: {validation_result['errors']}"
            )
        
        # Get hotel details
        hotel = hotel_service.get_hotel_by_id(request.hotel_id)
        if not hotel:
            raise HTTPException(
                status_code=404,
                detail=f"Hotel not found: {request.hotel_id}"
            )
        
        # Create booking
        booking = booking_service.create_booking(hotel, request.preferences)
        
        if booking:
            return JSONResponse(content={
                "success": True,
                "booking": booking,
                "message": "Booking confirmed successfully"
            })
        else:
            raise HTTPException(
                status_code=500,
                detail="Booking failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Booking error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Booking failed: {str(e)}"
        )

# Chat endpoint
@app.post("/chat")
@track_performance("chat")
async def chat(request: ChatRequest):
    """Chat with AI assistant"""
    try:
        # Process with conversation intelligence
        result = conversation_intelligence.process_user_input(request.message)
        
        return JSONResponse(content={
            "success": True,
            "response": result["response"],
            "intent": result["intent"].value,
            "response_type": result["response_type"],
            "hotels": result.get("hotels", []),
            "booking": result.get("booking")
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )

# Get hotel details endpoint
@app.get("/hotels/{hotel_id}")
@track_performance("hotel_details")
async def get_hotel_details(hotel_id: str):
    """Get detailed hotel information"""
    try:
        hotel = hotel_service.get_hotel_by_id(hotel_id)
        
        if hotel:
            return JSONResponse(content={
                "success": True,
                "hotel": hotel
            })
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Hotel not found: {hotel_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hotel details error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get hotel details: {str(e)}"
        )

# Get booking details endpoint
@app.get("/bookings/{booking_id}")
@track_performance("booking_details")
async def get_booking_details(booking_id: str):
    """Get booking information"""
    try:
        booking = booking_service.get_booking_by_id(booking_id)
        
        if booking:
            return JSONResponse(content={
                "success": True,
                "booking": booking
            })
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Booking not found: {booking_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Booking details error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get booking details: {str(e)}"
        )

# Cancel booking endpoint
@app.delete("/bookings/{booking_id}")
@track_performance("cancel_booking")
async def cancel_booking(booking_id: str):
    """Cancel a booking"""
    try:
        success = booking_service.cancel_booking(booking_id)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": "Booking cancelled successfully"
            })
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Booking not found: {booking_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel booking error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel booking: {str(e)}"
        )

# Popular destinations endpoint
@app.get("/destinations/popular")
@track_performance("popular_destinations")
async def get_popular_destinations():
    """Get popular hotel destinations"""
    try:
        destinations = hotel_service.get_popular_destinations()
        return JSONResponse(content={
            "success": True,
            "destinations": destinations
        })
        
    except Exception as e:
        logger.error(f"Popular destinations error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get popular destinations: {str(e)}"
        )

# Smart recommendations endpoint
@app.post("/recommendations")
@track_performance("recommendations")
async def get_recommendations(request: SearchRequest):
    """Get smart recommendations based on search"""
    try:
        # First search for hotels
        result = conversation_intelligence.process_user_input(request.query)
        
        if result.get("hotels"):
            recommendations = hotel_service.get_smart_recommendations(
                request.preferences or {},
                result["hotels"]
            )
            
            return JSONResponse(content={
                "success": True,
                "recommendations": recommendations
            })
        else:
            return JSONResponse(content={
                "success": False,
                "message": "No hotels found for recommendations"
            })
            
    except Exception as e:
        logger.error(f"Recommendations error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)}"
        )

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("AI Hotel Booking Assistant API starting up...")
    logger.info(f"Environment: {config.app.environment}")
    logger.info(f"Version: {config.app.version}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("AI Hotel Booking Assistant API shutting down...")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=config.is_development(),
        log_level=config.app.log_level.lower()
    )
