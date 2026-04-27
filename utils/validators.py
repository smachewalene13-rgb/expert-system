"""
Input Validators
Functions for validating user input data
"""

import re
from typing import Tuple, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ValidationResult:
    """Class to hold validation results"""
    is_valid: bool
    message: str = ''
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        self.is_valid = False

def validate_username(username: str) -> ValidationResult:
    """
    Validate username
    
    Rules:
    - 3-50 characters
    - Only letters, numbers, underscore, and dot
    - Must start with a letter
    """
    result = ValidationResult(is_valid=True)
    
    if not username:
        result.add_error('Username is required')
        return result
    
    if len(username) < 3:
        result.add_error('Username must be at least 3 characters long')
    
    if len(username) > 50:
        result.add_error('Username cannot exceed 50 characters')
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_.]{2,49}$', username):
        result.add_error('Username must start with a letter and contain only letters, numbers, underscore, or dot')
    
    return result

def validate_password(password: str, confirm_password: str = None) -> ValidationResult:
    """
    Validate password
    
    Rules:
    - At least 6 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    result = ValidationResult(is_valid=True)
    
    if not password:
        result.add_error('Password is required')
        return result
    
    if len(password) < 6:
        result.add_error('Password must be at least 6 characters long')
    
    if not re.search(r'[A-Z]', password):
        result.add_error('Password must contain at least one uppercase letter')
    
    if not re.search(r'[a-z]', password):
        result.add_error('Password must contain at least one lowercase letter')
    
    if not re.search(r'\d', password):
        result.add_error('Password must contain at least one digit')
    
    if confirm_password and password != confirm_password:
        result.add_error('Passwords do not match')
    
    return result

def validate_email(email: str) -> ValidationResult:
    """
    Validate email address
    
    Rules:
    - Valid email format
    - Not empty
    """
    result = ValidationResult(is_valid=True)
    
    if not email:
        result.add_error('Email is required')
        return result
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        result.add_error('Invalid email format')
    
    return result

def validate_age(age: str) -> ValidationResult:
    """
    Validate age
    
    Rules:
    - 0-120 years
    - Must be a number
    """
    result = ValidationResult(is_valid=True)
    
    if not age:
        # Age is optional, so empty is valid
        return result
    
    try:
        age_num = int(age)
        if age_num < 0:
            result.add_error('Age cannot be negative')
        elif age_num > 120:
            result.add_error('Age cannot exceed 120 years')
    except ValueError:
        result.add_error('Age must be a valid number')
    
    return result

def validate_symptoms(symptoms: List[str]) -> ValidationResult:
    """
    Validate symptoms list
    
    Rules:
    - At least one symptom
    - Each symptom between 2-50 characters
    - No duplicates
    """
    result = ValidationResult(is_valid=True)
    
    if not symptoms:
        result.add_error('Please enter at least one symptom')
        return result
    
    if len(symptoms) > 20:
        result.add_error('Cannot enter more than 20 symptoms at once')
    
    seen = set()
    for i, symptom in enumerate(symptoms):
        if not symptom or len(symptom.strip()) < 2:
            result.add_error(f'Symptom at position {i+1} is too short (min 2 characters)')
        elif len(symptom) > 50:
            result.add_error(f'Symptom "{symptom[:20]}..." is too long (max 50 characters)')
        
        symptom_lower = symptom.lower()
        if symptom_lower in seen:
            result.add_error(f'Duplicate symptom: "{symptom}"')
        seen.add(symptom_lower)
    
    return result

def validate_duration(duration: str) -> ValidationResult:
    """
    Validate symptom duration
    
    Rules:
    - Must be one of the allowed values
    """
    result = ValidationResult(is_valid=True)
    
    allowed_values = ['', 'less_than_24h', '1_3_days', '4_7_days', 'more_than_week']
    
    if duration and duration not in allowed_values:
        result.add_error('Invalid duration value')
    
    return result

def validate_phone(phone: str) -> ValidationResult:
    """
    Validate phone number
    
    Rules:
    - Optional field
    - If provided, must be valid phone format
    """
    result = ValidationResult(is_valid=True)
    
    if not phone:
        return result
    
    # Remove separators
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    if not cleaned.isdigit():
        result.add_error('Phone number should contain only digits and separators')
    elif len(cleaned) < 8:
        result.add_error('Phone number must be at least 8 digits')
    elif len(cleaned) > 15:
        result.add_error('Phone number cannot exceed 15 digits')
    
    return result

def validate_search_query(query: str) -> ValidationResult:
    """
    Validate search query
    
    Rules:
    - 2-100 characters
    - Not empty
    """
    result = ValidationResult(is_valid=True)
    
    if not query or not query.strip():
        result.add_error('Search query cannot be empty')
        return result
    
    if len(query) < 2:
        result.add_error('Search query must be at least 2 characters')
    
    if len(query) > 100:
        result.add_error('Search query cannot exceed 100 characters')
    
    return result

def validate_diagnosis_id(diagnosis_id: str) -> ValidationResult:
    """
    Validate diagnosis ID format
    
    Rules:
    - Must be a positive integer
    """
    result = ValidationResult(is_valid=True)
    
    try:
        id_num = int(diagnosis_id)
        if id_num <= 0:
            result.add_error('Diagnosis ID must be a positive number')
    except (ValueError, TypeError):
        result.add_error('Invalid diagnosis ID format')
    
    return result