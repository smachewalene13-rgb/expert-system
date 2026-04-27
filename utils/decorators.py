"""
Custom Decorators
Decorators for route protection, error handling, and logging
"""

import functools
import time
from datetime import datetime
from flask import flash, redirect, url_for, request, session, current_app
from flask_login import current_user
from functools import wraps

def admin_required(f):
    """
    Decorator to restrict access to admin users only
    
    Usage:
        @app.route('/admin')
        @admin_required
        def admin_panel():
            return "Admin only"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        if current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    """
    Decorator to restrict access to doctor and admin users
    
    Usage:
        @app.route('/medical-records')
        @doctor_required
        def medical_records():
            return "Doctor only"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        if current_user.role not in ['doctor', 'admin']:
            flash('Doctor access required.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def patient_required(f):
    """
    Decorator for patient-only access (or self data access)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        # Allow admin to access patient routes
        if current_user.role not in ['patient', 'admin']:
            flash('Access denied.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def handle_errors(default_message="An error occurred. Please try again."):
    """
    Decorator for handling exceptions in routes
    
    Usage:
        @app.route('/api/data')
        @handle_errors("Failed to fetch data")
        def get_data():
            # risky operation
            return data
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                current_app.logger.error(f"Error in {f.__name__}: {str(e)}")
                flash(default_message, 'danger')
                return redirect(url_for('index'))
        return decorated_function
    return decorator

def log_activity(activity_type: str):
    """
    Decorator to log user activities
    
    Usage:
        @app.route('/diagnose')
        @log_activity('diagnosis')
        def diagnose():
            return "Diagnosis page"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Log before execution
            if current_user.is_authenticated:
                current_app.logger.info(
                    f"User {current_user.username} performed {activity_type} "
                    f"at {datetime.now()}"
                )
            
            # Execute the function
            response = f(*args, **kwargs)
            
            # Log after execution if needed
            # current_app.logger.info(f"Completed {activity_type}")
            
            return response
        return decorated_function
    return decorator

def rate_limit(limit_per_minute: int = 60):
    """
    Simple rate limiting decorator (in-memory)
    
    Usage:
        @app.route('/api/diagnose')
        @rate_limit(10)
        def diagnose():
            return "Diagnosis"
    """
    def decorator(f):
        # Store request timestamps in memory
        request_counts = {}
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier (IP address or user ID)
            if current_user.is_authenticated:
                client_id = f"user_{current_user.id}"
            else:
                client_id = request.remote_addr
            
            current_time = time.time()
            minute_ago = current_time - 60
            
            # Clean old requests
            if client_id in request_counts:
                request_counts[client_id] = [t for t in request_counts[client_id] if t > minute_ago]
            else:
                request_counts[client_id] = []
            
            # Check rate limit
            if len(request_counts[client_id]) >= limit_per_minute:
                flash(f'Rate limit exceeded. Maximum {limit_per_minute} requests per minute.', 'danger')
                return redirect(url_for('index'))
            
            # Record this request
            request_counts[client_id].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def cache_result(timeout: int = 300):
    """
    Simple caching decorator (in-memory)
    
    Usage:
        @app.route('/api/conditions')
        @cache_result(3600)
        def get_conditions():
            return expensive_operation()
    """
    def decorator(f):
        cache = {}
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}_{str(args)}_{str(kwargs)}"
            
            # Check if cached and not expired
            if cache_key in cache:
                cached_data, timestamp = cache[cache_key]
                if time.time() - timestamp < timeout:
                    return cached_data
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            
            return result
        return decorated_function
    return decorator

def validate_json(required_fields: list = None):
    """
    Decorator to validate JSON request data
    
    Usage:
        @app.route('/api/diagnose', methods=['POST'])
        @validate_json(required_fields=['symptoms'])
        def diagnose():
            data = request.get_json()
            return process(data)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return {"error": "Content-Type must be application/json"}, 400
            
            data = request.get_json()
            
            if required_fields:
                for field in required_fields:
                    if field not in data:
                        return {"error": f"Missing required field: {field}"}, 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_https(f):
    """
    Decorator to enforce HTTPS (for production)
    
    Usage:
        @app.route('/secure')
        @require_https
        def secure_page():
            return "HTTPS only"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure:
            # Redirect to HTTPS
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url)
        return f(*args, **kwargs)
    return decorated_function

def maintenance_mode(f):
    """
    Decorator to enable maintenance mode
    
    Usage:
        @app.route('/feature')
        @maintenance_mode
        def feature():
            return "Feature"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if maintenance mode is enabled (could be from config or database)
        if current_app.config.get('MAINTENANCE_MODE', False):
            flash('System is under maintenance. Please try again later.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function