import logging
from logging.handlers import RotatingFileHandler
import os

os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("attendance_app")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=3)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)