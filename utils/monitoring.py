import logging
import time
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from utils.config import get_config

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    total_response_time: float = 0.0
    search_requests: int = 0
    booking_requests: int = 0
    error_types: Dict[str, int] = None
    
    def __post_init__(self):
        if self.error_types is None:
            self.error_types = {}

class MonitoringService:
    """Production monitoring service"""
    
    def __init__(self):
        self.config = get_config()
        self.metrics = PerformanceMetrics()
        self.request_times: List[float] = []
        self.start_time = time.time()
        
    def track_request(self, request_type: str, success: bool, response_time: float, error: str = None):
        """Track request metrics"""
        self.metrics.total_requests += 1
        self.request_times.append(response_time)
        self.metrics.total_response_time += response_time
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
            if error:
                error_type = error.split(':')[0] if ':' in error else error
                self.metrics.error_types[error_type] = self.metrics.error_types.get(error_type, 0) + 1
        
        # Track specific request types
        if request_type == 'search':
            self.metrics.search_requests += 1
        elif request_type == 'booking':
            self.metrics.booking_requests += 1
        
        # Update average response time
        self.metrics.avg_response_time = self.metrics.total_response_time / self.metrics.total_requests
        
        logger.info(f"Request tracked: {request_type} - Success: {success} - Time: {response_time:.3f}s")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        uptime = time.time() - self.start_time
        success_rate = (self.metrics.successful_requests / self.metrics.total_requests * 100) if self.metrics.total_requests > 0 else 100
        
        # Determine health status
        if success_rate >= 95 and self.metrics.avg_response_time < 2.0:
            status = "healthy"
        elif success_rate >= 90 and self.metrics.avg_response_time < 5.0:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "uptime_seconds": uptime,
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "total_requests": self.metrics.total_requests,
            "success_rate": round(success_rate, 2),
            "avg_response_time": round(self.metrics.avg_response_time, 3),
            "search_requests": self.metrics.search_requests,
            "booking_requests": self.metrics.booking_requests,
            "error_types": self.metrics.error_types,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get detailed metrics summary"""
        return {
            "performance": asdict(self.metrics),
            "system_info": {
                "version": self.config.app.version,
                "environment": "production" if self.config.is_production() else "development",
                "log_level": self.config.app.log_level
            },
            "recent_performance": {
                "last_10_requests": {
                    "avg_time": recent_avg_time,
                    "success_rate": recent_success_rate
                }
            }
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = PerformanceMetrics()
        self.request_times = []
        self.start_time = time.time()
        logger.info("Metrics reset")

# Global monitoring instance
monitoring_service = MonitoringService()

def track_performance(request_type: str):
    """Decorator to track function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                logger.error(f"Function {func.__name__} failed: {error}")
                raise
            finally:
                response_time = time.time() - start_time
                monitoring_service.track_request(request_type, success, response_time, error)
        
        return wrapper
    return decorator

def get_monitoring_service() -> MonitoringService:
    """Get global monitoring service instance"""
    return monitoring_service
