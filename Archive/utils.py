"""Utility functions for transcription pipeline."""

import os
import logging
from pathlib import Path
from typing import List
from datetime import timedelta


def setup_logging(log_file: str | Path) -> logging.Logger:
    """Configure logging to file and console."""
    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS.mmm format."""
    td = timedelta(seconds=seconds)
    h = td.seconds // 3600
    m = (td.seconds % 3600) // 60
    s = td.seconds % 60
    ms = td.microseconds // 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def parse_timestamp(timestamp: str) -> float:
    """Convert HH:MM:SS.mmm to seconds."""
    h, m, s = timestamp.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def cleanup_files(file_list: List[str], logger: logging.Logger = None) -> None:
    """Delete temporary files."""
    for filepath in file_list:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                if logger:
                    logger.info(f"Cleaned: {filepath}")
        except Exception as e:
            if logger:
                logger.warning(f"Failed to delete {filepath}: {e}")
