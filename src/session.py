"""
Session Management Module for TMS Dashboard.
Handles session creation for Flask-Session.
"""

from datetime import datetime

# Session configuration
SESSION_TIMEOUT_MINUTES = 30


def create_session(user_id):
    """
    Create a new session for a user.
    
    Args:
        user_id (str): Username for the session
    
    Returns:
        dict: Session dictionary with user_id, timestamps, etc.
    """
    now = datetime.now()
    
    return {
        'user_id': user_id,
        'login_time': now.isoformat(),
        'last_activity': now.isoformat(),
        'session_timeout_minutes': SESSION_TIMEOUT_MINUTES
    }
