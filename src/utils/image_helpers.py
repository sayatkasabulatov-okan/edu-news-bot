"""Helpers for handling images (local files, URLs, file_ids)"""
import os
from typing import Union
from loguru import logger


def prepare_photo(image_ref: str) -> Union[bytes, str]:
    """
    Prepare a photo reference for Telegram's send_photo.

    Handles three cases:
    - Local file path -> read and return bytes
    - HTTP/HTTPS URL -> return as-is (for scraped article images)
    - Telegram file_id -> return as-is

    Args:
        image_ref: Local file path, HTTP URL, or Telegram file_id

    Returns:
        bytes for local files, or the original string for URLs/file_ids
    """
    if not image_ref:
        return image_ref

    # Check if it's a local file
    if os.path.isfile(image_ref):
        logger.debug(f"Reading local image file: {image_ref}")
        with open(image_ref, 'rb') as f:
            return f.read()

    # Otherwise return as-is (URL or file_id)
    return image_ref
