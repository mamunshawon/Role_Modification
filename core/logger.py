import logging
from datetime import datetime
import os


def setup_logger():
    os.makedirs("logs", exist_ok=True)
    log_file = f'logs/run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(threadName)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ],
        force=True
    )

    logger = logging.getLogger()
    logger.info("Log file created: %s", log_file)
    return logger
