import logging
import json

class ColorFormatter(logging.Formatter):
    """Custom formatter to add color to log messages based on level."""
    COLOR_CODES = {
        "DEBUG": "\033[37m",  # White
        "INFO": "\033[32m",   # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"  # Reset color

    def format(self, record):
        log_color = self.COLOR_CODES.get(record.levelname, self.RESET)
        message = super().format(record)
        return f"{log_color}{message}{self.RESET}"

def log_error(logger, error_message, extra=None):
    if logger:
        full_message = _compose_message(error_message, extra)
        logger.error(full_message)

def log_info(logger, info_message, extra=None):
    if logger:
        full_message = _compose_message(info_message, extra)
        logger.info(full_message)

def log_warning(logger, warning_message, extra=None):
    if logger:
        full_message = _compose_message(warning_message, extra)
        logger.warning(full_message)

def log_debug(logger, debug_message, extra=None):
    if logger:
        full_message = _compose_message(debug_message, extra)
        logger.debug(full_message)

def _compose_message(message, extra):
    if extra:
        if isinstance(extra, dict):
            try:
                details = json.dumps(extra, default=str)
            except Exception:
                details = str(extra)
        else:
            details = str(extra)
        return f"{message} | {details}"
    return message

def setup_logger(name="project_logger", level=logging.DEBUG):
    """
    Set up a logger with the ColorFormatter.
    
    Args:
        name (str): Name of the logger.
        level (int): Logging level.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Apply the color formatter
    formatter = ColorFormatter("[%(levelname)s] %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)
    return logger