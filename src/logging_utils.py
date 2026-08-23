import os
import logging
from logging.handlers import RotatingFileHandler

from . import config

LOG_DIR = os.path.join(config.OUTPUT_DIR, "logs")
os.makedirs(LOG_DIR,exist_ok=True)
LOG_FILE= os.path.join(LOG_DIR, "app.log")

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configured = False

def _configure_root_handler():
    global _configured
    if _configured:
        return
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # rotate at 5MB, keep 3 old copies -- prevents the log file from growing
    # forever on a long-running deployed server

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_00_000, backupCount=3)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(console_handler)
    root.addHandler(file_handler)

    for noisy_logger in ["matplotlib", "PIL", "urllib3"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


    _configured = True

def get_logger(name):
    _configure_root_handler()
    return logging.getLogger(name)










