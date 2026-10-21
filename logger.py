import logging
from logging.handlers import RotatingFileHandler
import json
import os
from datetime import datetime
import threading
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    def format(self, record):
        # Create the base log record
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "logger_name": record.name,
            "user": getattr(record, 'user', 'anonymous'),
            "session_id": getattr(record, 'session_id', ''),
            "thread_id": threading.current_thread().ident,
            "thread_name": threading.current_thread().name
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in log_record and key not in ['name', 'msg', 'args', 'levelname', 
                                                    'levelno', 'pathname', 'filename', 
                                                    'module', 'lineno', 'funcName', 
                                                    'created', 'msecs', 'relativeCreated', 
                                                    'thread', 'threadName', 'processName', 
                                                    'process', 'getMessage', 'exc_info', 
                                                    'exc_text', 'stack_info']:
                log_record[key] = value
        
        return json.dumps(log_record, ensure_ascii=False)

class ContextFilter(logging.Filter):
    """
    Filter to add contextual information to log records
    """
    def filter(self, record):
        # Add default context if not already present
        if not hasattr(record, 'user'):
            record.user = getattr(logging, 'current_user', 'anonymous')
        if not hasattr(record, 'session_id'):
            record.session_id = getattr(logging, 'current_session_id', '')
        return True

def setup_logging(
    log_level: int = logging.DEBUG,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    max_file_size: int = 10485760,  # 10MB
    backup_count: int = 5,
    log_file: str = 'app.log'
):
    """
    Setup comprehensive logging with JSON formatting
    
    Args:
        log_level: Root logger level
        console_level: Console handler level
        file_level: File handler level
        max_file_size: Maximum size of log file before rotation (bytes)
        backup_count: Number of backup files to keep
        log_file: Path to the log file
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file) or '.'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    json_formatter = JSONFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    
    # File handler for JSON logs
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(json_formatter)
    
    # Create a separate handler for error logs
    error_log_file = log_file.replace('.log', '_errors.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Add context filter
    root_logger.addFilter(ContextFilter())
    
    # Log setup completion
    root_logger.info("Logging system initialized", extra={
        'setup_time': datetime.now().isoformat(),
        'log_level': logging.getLevelName(log_level),
        'log_file': log_file
    })

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    return logger

def log_user_action(
    logger_instance: logging.Logger,
    user_id: str,
    action: str,
    session_id: str = '',
    extra_data: Dict[str, Any] = None
):
    """
    Log a user action with contextual information
    
    Args:
        logger_instance: Logger instance to use
        user_id: ID of the user performing the action
        action: Description of the action
        session_id: Session identifier
        extra_data: Additional data to log
    """
    extra = {
        'user': user_id,
        'session_id': session_id
    }
    
    if extra_data:
        extra.update(extra_data)
    
    logger_instance.info(f"User action: {action}", extra=extra)

def log_api_request(
    logger_instance: logging.Logger,
    endpoint: str,
    method: str,
    status_code: int,
    user_id: str = 'anonymous',
    session_id: str = '',
    response_time: float = 0.0,
    extra_data: Dict[str, Any] = None
):
    """
    Log an API request with relevant information
    
    Args:
        logger_instance: Logger instance to use
        endpoint: API endpoint
        method: HTTP method
        status_code: HTTP status code
        user_id: User ID making the request
        session_id: Session identifier
        response_time: Time taken to process the request
        extra_data: Additional data to log
    """
    extra = {
        'user': user_id,
        'session_id': session_id,
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'response_time_ms': response_time * 1000
    }
    
    if extra_data:
        extra.update(extra_data)
    
    level = logging.INFO if status_code < 400 else logging.WARNING
    message = f"API {method} {endpoint} - Status: {status_code}"
    
    if logger_instance.isEnabledFor(level):
        logger_instance.log(level, message, extra=extra)

def log_error_with_context(
    logger_instance: logging.Logger,
    error: Exception,
    context: str = '',
    user_id: str = 'anonymous',
    session_id: str = '',
    extra_data: Dict[str, Any] = None
):
    """
    Log an error with contextual information
    
    Args:
        logger_instance: Logger instance to use
        error: Exception object
        context: Context of where the error occurred
        user_id: User ID when error occurred
        session_id: Session identifier
        extra_data: Additional data to log
    """
    extra = {
        'user': user_id,
        'session_id': session_id,
        'error_type': type(error).__name__,
        'context': context
    }
    
    if extra_data:
        extra.update(extra_data)
    
    logger_instance.error(
        f"Error occurred in {context}: {str(error)}",
        extra=extra,
        exc_info=True
    )

# Global logger instance
def get_app_logger(name: str = __name__) -> logging.Logger:
    """
    Get the main application logger
    
    Args:
        name: Name for the logger (defaults to current module name)
        
    Returns:
        Application logger instance
    """
    return get_logger(name)

# Initialize logging when module is imported
if __name__ != '__main__':
    setup_logging()