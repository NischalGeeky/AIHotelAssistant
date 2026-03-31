#!/usr/bin/env python3
"""
Production deployment script for AI Hotel Booking Assistant
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all dependencies are installed"""
    logger.info("Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'streamlit',
        'langchain',
        'scikit-learn',
        'numpy',
        'pydantic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing packages: {missing_packages}")
        logger.info("Install missing packages with: pip install -r requirements.txt")
        return False
    
    logger.info("All dependencies are installed")
    return True

def check_environment():
    """Check environment variables"""
    logger.info("Checking environment configuration...")
    
    required_env_vars = [
        'GROQ_API_KEY'
    ]
    
    missing_env_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_env_vars.append(var)
    
    if missing_env_vars:
        logger.error(f"Missing environment variables: {missing_env_vars}")
        logger.info("Set up .env file with required variables")
        return False
    
    logger.info("Environment variables are configured")
    return True

def run_health_checks():
    """Run health checks on services"""
    logger.info("Running health checks...")
    
    try:
        # Test hotel service
        from services.enhanced_hotel_service import EnhancedHotelService
        hotel_service = EnhancedHotelService()
        hotels = hotel_service.search_hotels_hybrid({'location': 'Bangalore'})
        logger.info(f"Hotel service health check: {len(hotels)} hotels found")
        
        # Test booking service
        from services.booking_service import BookingService
        booking_service = BookingService()
        logger.info("Booking service health check: OK")
        
        # Test conversation intelligence
        from utils.intelligence import ConversationIntelligence
        conv_intel = ConversationIntelligence(hotel_service)
        result = conv_intel.process_user_input("test query")
        logger.info(f"Conversation intelligence health check: {result['intent'].value}")
        
        # Test monitoring
        from utils.monitoring import get_monitoring_service
        monitoring = get_monitoring_service()
        health = monitoring.get_health_status()
        logger.info(f"Monitoring health check: {health['status']}")
        
        logger.info("All health checks passed")
        return True
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

def start_streamlit():
    """Start Streamlit application"""
    logger.info("Starting Streamlit application...")
    
    try:
        # Run Streamlit in background
        cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "true",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"Streamlit started with PID: {process.pid}")
        logger.info("Streamlit available at: http://localhost:8501")
        
        return process
        
    except Exception as e:
        logger.error(f"Failed to start Streamlit: {str(e)}")
        return None

def start_api():
    """Start FastAPI application"""
    logger.info("Starting FastAPI application...")
    
    try:
        # Run API server
        cmd = [
            sys.executable, "-m", "uvicorn", "api:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--workers", "4"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"FastAPI started with PID: {process.pid}")
        logger.info("API available at: http://localhost:8000")
        logger.info("API docs available at: http://localhost:8000/docs")
        
        return process
        
    except Exception as e:
        logger.error(f"Failed to start FastAPI: {str(e)}")
        return None

def main():
    """Main deployment function"""
    logger.info("=== AI Hotel Booking Assistant Deployment ===")
    
    # Check prerequisites
    if not check_dependencies():
        sys.exit(1)
    
    if not check_environment():
        sys.exit(1)
    
    if not run_health_checks():
        sys.exit(1)
    
    # Parse deployment mode
    mode = os.getenv("DEPLOYMENT_MODE", "streamlit").lower()
    
    if mode == "api":
        logger.info("Deploying in API mode...")
        api_process = start_api()
        if api_process:
            try:
                api_process.wait()
            except KeyboardInterrupt:
                logger.info("Shutting down API server...")
                api_process.terminate()
    else:
        logger.info("Deploying in Streamlit mode...")
        streamlit_process = start_streamlit()
        if streamlit_process:
            try:
                streamlit_process.wait()
            except KeyboardInterrupt:
                logger.info("Shutting down Streamlit server...")
                streamlit_process.terminate()
    
    logger.info("Deployment completed")

if __name__ == "__main__":
    main()
