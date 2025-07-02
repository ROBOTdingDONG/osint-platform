"""
Logging configuration for the OSINT Platform
Provides structured logging with appropriate formatting and levels
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any

from app.core.config import settings


def setup_logging() -> None:
    """Configure application logging"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Logging configuration
    logging_config: Dict[str, Any] = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '[{asctime}] {levelname:<8} {name:<15} {message}',
                'style': '{',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '{levelname:<8} {name:<15} {message}',
                'style': '{'
            },
            'json': {
                'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
                'datefmt': '%Y-%m-%dT%H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'detailed' if settings.DEBUG else 'simple',
                'stream': sys.stdout
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': logging.INFO,
                'formatter': 'detailed',
                'filename': log_dir / 'osint_platform.log',
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': logging.ERROR,
                'formatter': 'detailed',
                'filename': log_dir / 'errors.log',
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            'app': {
                'level': log_level,
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'uvicorn': {
                'level': logging.INFO,
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn.error': {
                'level': logging.INFO,
                'handlers': ['console', 'error_file'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': logging.INFO,
                'handlers': ['console'],
                'propagate': False
            },
            'motor': {
                'level': logging.WARNING,
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'pymongo': {
                'level': logging.WARNING,
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console', 'file', 'error_file']
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Set up request ID logging (for tracing)
    setup_request_logging()
    
    logger = logging.getLogger('app.logging')
    logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}, Environment: {settings.ENVIRONMENT}")


def setup_request_logging():
    """Setup request ID logging for tracing"""
    import contextvars
    
    # Create context variable for request ID
    request_id_var = contextvars.ContextVar('request_id', default='')
    
    class RequestIDFilter(logging.Filter):
        """Add request ID to log records"""
        
        def filter(self, record):
            request_id = request_id_var.get('')
            if request_id:
                record.request_id = request_id
                record.getMessage = lambda: f"[{request_id}] {record.getMessage()}"
            return True
    
    # Add filter to all handlers
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestIDFilter())


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""
    return logging.getLogger(f"app.{name}")


class SecurityLogger:
    """Security-focused logging utilities"""
    
    def __init__(self):
        self.logger = get_logger('security')
    
    def log_auth_attempt(self, email: str, success: bool, ip_address: str = None):
        """Log authentication attempts"""
        status = "SUCCESS" if success else "FAILED"
        ip_info = f" from {ip_address}" if ip_address else ""
        self.logger.info(f"Authentication {status} for {email}{ip_info}")
    
    def log_auth_failure(self, email: str, reason: str, ip_address: str = None):
        """Log authentication failures with details"""
        ip_info = f" from {ip_address}" if ip_address else ""
        self.logger.warning(f"Authentication FAILED for {email}: {reason}{ip_info}")
    
    def log_api_key_usage(self, key_id: str, endpoint: str, ip_address: str = None):
        """Log API key usage"""
        ip_info = f" from {ip_address}" if ip_address else ""
        self.logger.info(f"API key {key_id} accessed {endpoint}{ip_info}")
    
    def log_data_access(self, user_id: str, resource: str, action: str):
        """Log data access for audit trail"""
        self.logger.info(f"User {user_id} performed {action} on {resource}")
    
    def log_suspicious_activity(self, description: str, ip_address: str = None, user_id: str = None):
        """Log suspicious activities"""
        user_info = f" (User: {user_id})" if user_id else ""
        ip_info = f" from {ip_address}" if ip_address else ""
        self.logger.warning(f"SUSPICIOUS ACTIVITY: {description}{user_info}{ip_info}")


class PerformanceLogger:
    """Performance monitoring logging"""
    
    def __init__(self):
        self.logger = get_logger('performance')
    
    def log_slow_query(self, query_type: str, duration: float, details: str = None):
        """Log slow database queries"""
        detail_info = f" - {details}" if details else ""
        self.logger.warning(f"Slow {query_type} query: {duration:.2f}s{detail_info}")
    
    def log_api_performance(self, endpoint: str, method: str, duration: float, status_code: int):
        """Log API endpoint performance"""
        self.logger.info(f"{method} {endpoint} - {status_code} - {duration:.3f}s")
    
    def log_memory_usage(self, process_name: str, memory_mb: float):
        """Log memory usage"""
        self.logger.info(f"Memory usage - {process_name}: {memory_mb:.1f}MB")


class DataLogger:
    """Data collection and processing logging"""
    
    def __init__(self):
        self.logger = get_logger('data')
    
    def log_data_collection(self, source: str, records_collected: int, success: bool):
        """Log data collection activities"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Data collection {status} - {source}: {records_collected} records")
    
    def log_data_processing(self, processor: str, records_processed: int, duration: float):
        """Log data processing activities"""
        self.logger.info(f"Data processing - {processor}: {records_processed} records in {duration:.2f}s")
    
    def log_analysis_completion(self, analysis_type: str, data_points: int, results: dict):
        """Log analysis completion"""
        self.logger.info(f"Analysis completed - {analysis_type}: {data_points} data points, results: {results}")


# Create singleton instances
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()
data_logger = DataLogger()


# Utility functions
def mask_sensitive_data(data: str, mask_char: str = "*", show_last: int = 4) -> str:
    """Mask sensitive data for logging"""
    if len(data) <= show_last:
        return mask_char * len(data)
    return mask_char * (len(data) - show_last) + data[-show_last:]


def safe_log_dict(data: dict, sensitive_keys: list = None) -> dict:
    """Safely log dictionary data by masking sensitive keys"""
    if sensitive_keys is None:
        sensitive_keys = ['password', 'token', 'key', 'secret', 'api_key']
    
    safe_data = {}
    for key, value in data.items():
        if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            safe_data[key] = mask_sensitive_data(str(value))
        else:
            safe_data[key] = value
    
    return safe_data


# Export commonly used loggers and functions
__all__ = [
    'setup_logging',
    'get_logger',
    'security_logger',
    'performance_logger', 
    'data_logger',
    'mask_sensitive_data',
    'safe_log_dict'
]