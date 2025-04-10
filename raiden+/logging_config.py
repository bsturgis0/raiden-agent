import logging
import logging.handlers
from pathlib import Path
import json
from datetime import datetime

def setup_logging(app_name: str = "raiden"):
    """Configure application logging"""
    log_dir = Path.home() / f".{app_name}" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Main log file
    main_handler = logging.handlers.RotatingFileHandler(
        log_dir / "raiden.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    
    # Error log file
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10_000_000,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    
    # Audit log for sensitive operations
    audit_handler = logging.handlers.RotatingFileHandler(
        log_dir / "audit.log",
        maxBytes=10_000_000,
        backupCount=10
    )
    
    # Formatters
    main_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    audit_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - AUDIT - %(message)s'
    )
    
    main_handler.setFormatter(main_formatter)
    error_handler.setFormatter(main_formatter)
    audit_handler.setFormatter(audit_formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)
    
    # Audit logger
    audit_logger = logging.getLogger('audit')
    audit_logger.addHandler(audit_handler)
    
    return root_logger, audit_logger
