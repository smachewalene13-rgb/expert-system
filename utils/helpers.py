"""
Helper Functions
Common utility functions used throughout the application
"""

import re
import hashlib
from datetime import datetime, date
from typing import Optional, Any

def format_date(date_obj: Optional[datetime], format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format a datetime object to string
    
    Args:
        date_obj: Datetime object to format
        format_str: Format string (default: '%Y-%m-%d %H:%M:%S')
    
    Returns:
        Formatted date string or 'N/A' if date_obj is None
    """
    if date_obj is None:
        return 'N/A'
    return date_obj.strftime(format_str)

def format_date_short(date_obj: Optional[datetime]) -> str:
    """Format date to short format (YYYY-MM-DD)"""
    return format_date(date_obj, '%Y-%m-%d')

def calculate_age(birth_date: date) -> int:
    """
    Calculate age from birth date
    
    Args:
        birth_date: Date of birth
    
    Returns:
        Age in years
    """
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def sanitize_input(text: str, max_length: int = 500) -> str:
    """
    Sanitize user input by removing special characters and trimming
    
    Args:
        text: Input string to sanitize
        max_length: Maximum length of output
    
    Returns:
        Sanitized string
    """
    if not text:
        return ''
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove special characters (keep alphanumeric, spaces, basic punctuation)
    text = re.sub(r'[^\w\s\-.,!?]', '', text)
    
    # Trim to max length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Strip whitespace
    return text.strip()

def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to specified length and add suffix if truncated
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: String to append if truncated
    
    Returns:
        Truncated text
    """
    if not text:
        return ''
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def generate_id(prefix: str = '', length: int = 8) -> str:
    """
    Generate a unique ID
    
    Args:
        prefix: Optional prefix for the ID
        length: Length of the random part
    
    Returns:
        Unique ID string
    """
    import random
    import string
    
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    if prefix:
        return f"{prefix}_{timestamp}_{random_part}"
    return f"{timestamp}_{random_part}"

def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone_format(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if it's a valid phone number (8-15 digits)
    return cleaned.isdigit() and 8 <= len(cleaned) <= 15

def parse_symptoms(symptoms_text: str) -> list:
    """
    Parse comma-separated symptoms into list
    
    Args:
        symptoms_text: Comma-separated symptoms string
    
    Returns:
        List of individual symptoms
    """
    if not symptoms_text:
        return []
    
    # Split by comma and clean each symptom
    symptoms = [s.strip().lower() for s in symptoms_text.split(',')]
    # Remove empty strings
    symptoms = [s for s in symptoms if s]
    return symptoms

def join_symptoms(symptoms_list: list) -> str:
    """
    Join symptom list into comma-separated string
    
    Args:
        symptoms_list: List of symptoms
    
    Returns:
        Comma-separated string of symptoms
    """
    if not symptoms_list:
        return ''
    
    return ', '.join(symptoms_list)

def get_severity_color(severity: str) -> str:
    """
    Get Bootstrap color class for severity level
    
    Args:
        severity: Severity level (mild, moderate, severe)
    
    Returns:
        Bootstrap color class
    """
    colors = {
        'mild': 'success',
        'moderate': 'warning',
        'severe': 'danger',
        'high': 'danger',
        'medium': 'warning',
        'low': 'success'
    }
    return colors.get(severity.lower(), 'secondary')

def get_confidence_class(confidence: float) -> str:
    """
    Get Bootstrap color class based on confidence score
    
    Args:
        confidence: Confidence score (0-100)
    
    Returns:
        Bootstrap color class
    """
    if confidence >= 70:
        return 'success'
    elif confidence >= 40:
        return 'warning'
    else:
        return 'danger'

def hash_text(text: str) -> str:
    """
    Create SHA-256 hash of text
    
    Args:
        text: Text to hash
    
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(text.encode()).hexdigest()

def is_valid_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid URL, False otherwise
    """
    pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*/?'
    return bool(re.match(pattern, url))

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()