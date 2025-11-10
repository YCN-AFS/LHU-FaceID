"""Logger setup for LHU FaceID system."""
from loguru import logger
import sys
import config as cfg

# Configure logger
logger.remove()  # Remove default handler

# Add console handler
logger.add(
    sys.stderr,
    format=cfg.config.logging['format'],
    level=cfg.config.logging['level'],
    colorize=True
)

# Add file handler
logger.add(
    "logs/app_{time}.log",
    format=cfg.config.logging['format'],
    level=cfg.config.logging['level'],
    rotation=cfg.config.logging['rotation'],
    retention=cfg.config.logging['retention'],
    compression="zip"
)

# Add error file handler
logger.add(
    "logs/error_{time}.log",
    format=cfg.config.logging['format'],
    level="ERROR",
    rotation=cfg.config.logging['rotation'],
    retention=cfg.config.logging['retention'],
    compression="zip"
)

