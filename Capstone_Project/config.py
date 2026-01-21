import yaml
import os
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import logging
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    # Database (for Auth)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "users.db")
    
    # App Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    APP_TITLE: str = "AI Product Evaluator Pro"
    APP_VERSION: str = "2.0.0"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # Business Rules (The Magic Numbers)
    DEFAULT_POSITIVE_THRESHOLD: float = 0.2
    DEFAULT_NEGATIVE_THRESHOLD: float = -0.1
    MAX_FILE_SIZE_MB: int = 200
    MAX_BATCH_SIZE: int = 1000
    DEFAULT_ANALYSIS_TIMEOUT: int = 300  # seconds
    
    # Cache Settings
    USE_REDIS: bool = os.getenv("USE_REDIS", "False").lower() == "true"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DEFAULT_CACHE_TTL: int = 3600  # 1 hour
    
    # API Settings
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "100"))  # requests per minute
    API_MAX_RETRIES: int = 3
    API_TIMEOUT: int = 30  # seconds
    
    # File Upload Settings
    ALLOWED_FILE_TYPES: list = field(default_factory=lambda: ["csv"])
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "app.log")
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Security Settings
    SESSION_TIMEOUT: int = 3600  # 1 hour
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_DURATION: int = 900  # 15 minutes
    
    # Email Settings (if needed)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USER: str = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    
    # Translation Settings
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
    SUPPORTED_LANGUAGES: list = field(default_factory=lambda: ["en", "es", "fr", "de", "it"])
    
    # Model Settings
    SENTIMENT_MODEL_VERSION: str = "v1.0"
    CONFIDENCE_THRESHOLD: float = 0.7
    
    @classmethod
    def load(cls, filepath: str = "config.yaml", env_prefix: str = "APP_"):
        """
        Loads config from YAML, falls back to environment variables and defaults
        
        Args:
            filepath: Path to the YAML config file
            env_prefix: Prefix for environment variables (e.g., "APP_" for APP_DEBUG)
        """
        config_dict = {}
        
        # Load from YAML file if it exists
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f) or {}
                
                # Filter out keys that don't exist in our dataclass
                for key, value in yaml_config.items():
                    if key in cls.__annotations__:
                        config_dict[key] = value
                    else:
                        logger.warning(f"Unknown configuration key in {filepath}: {key}")
                
                logger.info(f"Configuration loaded from {filepath}")
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML config file {filepath}: {e}")
            except Exception as e:
                logger.error(f"Error loading config file {filepath}: {e}")
        
        # Override with environment variables
        for field_name in cls.__annotations__:
            env_var = f"{env_prefix}{field_name}"
            env_value = os.getenv(env_var)
            
            if env_value is not None:
                # Convert environment variable to the correct type
                expected_type = cls.__annotations__[field_name]
                
                try:
                    if expected_type == bool:
                        config_dict[field_name] = env_value.lower() == "true"
                    elif expected_type == int:
                        config_dict[field_name] = int(env_value)
                    elif expected_type == float:
                        config_dict[field_name] = float(env_value)
                    elif expected_type == str:
                        config_dict[field_name] = env_value
                    elif expected_type == list:
                        # Assume comma-separated values for lists
                        config_dict[field_name] = [item.strip() for item in env_value.split(',')]
                    else:
                        config_dict[field_name] = env_value
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not convert environment variable {env_var} to {expected_type}: {e}")
        
        # Create instance with defaults, then update with loaded values
        config = cls()
        
        # Update the config instance with loaded values
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Validate configuration
        config.validate()
        
        return config
    
    def validate(self) -> bool:
        """
        Validates the configuration settings
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        errors = []
        
        # Validate thresholds
        if self.DEFAULT_POSITIVE_THRESHOLD <= self.DEFAULT_NEGATIVE_THRESHOLD:
            errors.append("DEFAULT_POSITIVE_THRESHOLD must be greater than DEFAULT_NEGATIVE_THRESHOLD")
        
        # Validate file size
        if self.MAX_FILE_SIZE_MB <= 0:
            errors.append("MAX_FILE_SIZE_MB must be greater than 0")
        
        # Validate batch size
        if self.MAX_BATCH_SIZE <= 0:
            errors.append("MAX_BATCH_SIZE must be greater than 0")
        
        # Validate timeout
        if self.DEFAULT_ANALYSIS_TIMEOUT <= 0:
            errors.append("DEFAULT_ANALYSIS_TIMEOUT must be greater than 0")
        
        # Validate cache TTL
        if self.DEFAULT_CACHE_TTL <= 0:
            errors.append("DEFAULT_CACHE_TTL must be greater than 0")
        
        # Validate API rate limit
        if self.API_RATE_LIMIT <= 0:
            errors.append("API_RATE_LIMIT must be greater than 0")
        
        # Validate session timeout
        if self.SESSION_TIMEOUT <= 0:
            errors.append("SESSION_TIMEOUT must be greater than 0")
        
        # Validate login attempts
        if self.MAX_LOGIN_ATTEMPTS <= 0:
            errors.append("MAX_LOGIN_ATTEMPTS must be greater than 0")
        
        # Validate lockout duration
        if self.LOGIN_LOCKOUT_DURATION <= 0:
            errors.append("LOGIN_LOCKOUT_DURATION must be greater than 0")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        logger.info("Configuration validation passed")
        return True
    
    def save_to_yaml(self, filepath: str = "config.yaml"):
        """
        Saves the current configuration to a YAML file
        
        Args:
            filepath: Path to save the configuration file
        """
        try:
            # Convert dataclass to dictionary
            config_dict = {}
            for field_name in self.__annotations__:
                value = getattr(self, field_name)
                if isinstance(value, (list, tuple, set)):
                    # Convert to list for YAML serialization
                    config_dict[field_name] = list(value)
                else:
                    config_dict[field_name] = value
            
            # Create directory if it doesn't exist
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # Write to YAML file
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Configuration saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving configuration to {filepath}: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the configuration to a dictionary
        
        Returns:
            Dict containing all configuration values
        """
        result = {}
        for field_name in self.__annotations__:
            result[field_name] = getattr(self, field_name)
        return result
    
    def to_json(self) -> str:
        """
        Converts the configuration to JSON string
        
        Returns:
            JSON string representation of the configuration
        """
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def get_sensitive_fields(self) -> list:
        """
        Returns a list of sensitive fields that should be masked in logs
        
        Returns:
            List of sensitive field names
        """
        return ['SECRET_KEY', 'EMAIL_PASSWORD', 'DATABASE_URL']
    
    def mask_sensitive_info(self) -> Dict[str, Any]:
        """
        Returns a dictionary with sensitive information masked
        
        Returns:
            Dictionary with sensitive fields masked
        """
        result = self.to_dict()
        for field_name in self.get_sensitive_fields():
            if field_name in result and result[field_name]:
                result[field_name] = "***MASKED***"
        return result

# Global configuration instance
_config_instance: Optional[AppConfig] = None

def get_config() -> AppConfig:
    """
    Get the global configuration instance
    
    Returns:
        AppConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig.load()
    return _config_instance

# Convenience functions
def get_database_url() -> str:
    """Get the database URL from configuration"""
    return get_config().DATABASE_URL

def get_app_title() -> str:
    """Get the application title from configuration"""
    return get_config().APP_TITLE

def get_secret_key() -> str:
    """Get the secret key from configuration"""
    return get_config().SECRET_KEY

def is_debug_mode() -> bool:
    """Check if the application is in debug mode"""
    return get_config().DEBUG

def get_upload_folder() -> str:
    """Get the upload folder path from configuration"""
    return get_config().UPLOAD_FOLDER

def get_max_file_size_mb() -> int:
    """Get the maximum file size from configuration"""
    return get_config().MAX_FILE_SIZE_MB

def get_positive_threshold() -> float:
    """Get the positive sentiment threshold from configuration"""
    return get_config().DEFAULT_POSITIVE_THRESHOLD

def get_negative_threshold() -> float:
    """Get the negative sentiment threshold from configuration"""
    return get_config().DEFAULT_NEGATIVE_THRESHOLD

def get_cache_ttl() -> int:
    """Get the default cache TTL from configuration"""
    return get_config().DEFAULT_CACHE_TTL

def get_api_rate_limit() -> int:
    """Get the API rate limit from configuration"""
    return get_config().API_RATE_LIMIT

def get_session_timeout() -> int:
    """Get the session timeout from configuration"""
    return get_config().SESSION_TIMEOUT