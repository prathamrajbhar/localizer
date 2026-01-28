"""
Logging configuration using Loguru
"""
import sys
from loguru import logger
from app.core.config import get_settings

settings = get_settings()


def setup_logger():
    """Configure logger with rich formatting"""
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO" if settings.ENVIRONMENT == "production" else "DEBUG"
    )
    
    # Add file logger
    logger.add(
        "/app/logs/app.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO"
    )
    
    # Add error file logger
    logger.add(
        "/app/logs/error.log",
        rotation="500 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR"
    )
    
    return logger


# Initialize logger
app_logger = setup_logger()

