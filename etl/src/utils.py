"""
Utility functions
"""
import logging
from datetime import datetime
from pathlib import Path
from config.settings import LOGS_DIR


def setup_logging(log_file: str = None):
    """
    Setup logging configuration
    
    Args:
        log_file: Optional log file name (default: initial_load_YYYYMMDD_HHMMSS.log)
    """
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"initial_load_{timestamp}.log"
    
    log_path = LOGS_DIR / log_file
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter('%(message)s')
    
    # File handler (detailed)
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler (simple)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info(f"Logging initialized. Log file: {log_path}")


def calculate_date_range_for_initial_load():
    """
    Calculate the appropriate start date for initial load
    Returns start date that will capture last 3 FY + 4 quarters
    """
    # For simplicity, use a fixed date that covers 3+ years
    return "2022-01-01"


def print_progress_summary(success_count: int, failed_count: int, skipped_count: int, total: int):
    """Print a summary of the data load progress"""
    print("\n" + "="*80)
    print("DATA LOAD SUMMARY")
    print("="*80)
    print(f"Total companies: {total}")
    print(f"✓ Successfully processed: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"⊘ Skipped: {skipped_count}")
    print(f"Success rate: {(success_count/total)*100:.1f}%")
    print("="*80)