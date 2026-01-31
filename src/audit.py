"""
Audit Logging Module for TMS Dashboard.
Provides high-level audit logging functionality for user actions.
"""

import time
from functools import wraps
from src.audit_db import log_action


# Tracked action types
TRACKED_ACTIONS = {
    'Trans-Begin': 'Begin transition action',
    'PE-Enable': 'Enable PE action',
    'T-Enable': 'Enable T action',
    'PE-Finalize': 'Finalize PE action',
    'PE-Direct': 'Direct PE action'
}


def get_client_ip(request):
    """
    Extract client IP address from Flask request object.
    
    Args:
        request: Flask request object
    
    Returns:
        str: Client IP address
    """
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ.get('HTTP_X_FORWARDED_FOR').split(',')[0]
    return request.remote_addr or 'unknown'


def audit_action(action_type):
    """
    Decorator to automatically log user actions.
    
    Usage:
        @app.route('/api/transition/state', methods=['POST'])
        @audit_action('Trans-Begin')
        def transition_state():
            # Your code here
            pass
    
    Args:
        action_type (str): Type of action being performed
    
    Returns:
        function: Decorated function that logs action
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session, request
            
            start_time = time.time()
            customer_ids = None
            status = 'success'
            error_message = None
            result = None
            
            try:
                # Extract customer_ids from request if available
                if request.method == 'POST':
                    data = request.get_json() or {}
                    customer_ids = data.get('customer_ids') or data.get('customer_id')
                elif request.method == 'GET':
                    customer_ids = request.args.get('customer_ids') or request.args.get('customer_id')
                
                # Extract from URL path if it's a customer_id parameter
                if not customer_ids and 'customer_id' in kwargs:
                    customer_ids = kwargs.get('customer_id')
                
                # Execute the wrapped function
                result = f(*args, **kwargs)
                
                return result
            
            except Exception as e:
                status = 'failure'
                error_message = str(e)
                raise
            
            finally:
                # Always log the action
                user_id = session.get('user_id', 'unknown')
                duration_ms = int((time.time() - start_time) * 1000)
                ip_address = get_client_ip(request)
                
                log_action(
                    user_id=user_id,
                    action_type=action_type,
                    customer_ids=customer_ids,
                    ip_address=ip_address,
                    status=status,
                    error_message=error_message,
                    duration_ms=duration_ms
                )
        
        return decorated_function
    return decorator


def log_user_action(user_id, action_type, customer_ids=None, ip_address=None,
                    status='success', error_message=None, duration_ms=None):
    """
    Manually log a user action.
    
    Args:
        user_id (str): Username who performed the action
        action_type (str): Type of action
        customer_ids (list or str): Customer ID(s) affected
        ip_address (str): Source IP address
        status (str): 'success' or 'failure'
        error_message (str): Error message if failed
        duration_ms (int): Duration of action in milliseconds
    
    Returns:
        int: ID of the logged action or None if failed
    """
    if action_type not in TRACKED_ACTIONS:
        print(f"Warning: Untracked action type: {action_type}")
    
    return log_action(
        user_id=user_id,
        action_type=action_type,
        customer_ids=customer_ids,
        ip_address=ip_address,
        status=status,
        error_message=error_message,
        duration_ms=duration_ms
    )


def is_tracked_action(action_type):
    """
    Check if an action type is tracked in the audit system.
    
    Args:
        action_type (str): Action type to check
    
    Returns:
        bool: True if tracked, False otherwise
    """
    return action_type in TRACKED_ACTIONS


def get_tracked_actions():
    """
    Get a dictionary of all tracked action types.
    
    Returns:
        dict: Dictionary with action_type as key and description as value
    """
    return TRACKED_ACTIONS.copy()
