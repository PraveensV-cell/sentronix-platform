from pathlib import Path

from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    LOG_DIR / "sentronix.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=True,
    level="INFO",
)

logger.add(
    sink=lambda msg: print(msg, end=""),
    colorize=True,
    level="INFO",
)

app_logger = logger
