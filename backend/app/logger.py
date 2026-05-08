import logging
import sys
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)

    app_env = os.getenv("APP_ENV", "development")

    if app_env == "development":
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)-5s | %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        fmt = logging.Formatter(
            '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )

    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler (production only)
    if app_env == "production":
        os.makedirs("logs", exist_ok=True)
        file_handler = RotatingFileHandler(
            "logs/agent.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    return logger


logger = setup_logger("voice-agent", os.getenv("LOG_LEVEL", "INFO"))
