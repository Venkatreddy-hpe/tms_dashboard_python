"""
Authentication Module for TMS Dashboard.
Handles user credential validation and authentication.
"""

# User credentials
USERS = {
    'admin': 'Arubatms@123',
    'vijay': 'Arubatms@123',
    'harish': 'Arubatms@123',
    'sriram': 'Arubatms@123',
    'fagun': 'Arubatms@123',
    'leena': 'Arubatms@123',
    'karthik': 'Arubatms@123',
    'dinesh': 'Arubatms@123',
    'swaathi': 'Arubatms@123',
    'jagadesh': 'Arubatms@123',
    'abdul': 'Arubatms@123',
    'lakshmi': 'Arubatms@123',
    'akhil': 'Arubatms@123',
    'selvan': 'Arubatms@123',
    'prasad': 'Arubatms@123',
    'manohar': 'Arubatms@123',
    'devraj': 'Arubatms@123'
}


def authenticate_user(username, password):
    """
    Authenticate a user by validating username and password.
    
    Args:
        username (str): Username to authenticate
        password (str): Password to validate
    
    Returns:
        bool: True if credentials are valid, False otherwise
    """
    if not username or not password:
        return False
    
    return USERS.get(username) == password


def is_valid_username(username):
    """
    Check if a username is valid (exists in the system).
    
    Args:
        username (str): Username to check
    
    Returns:
        bool: True if username exists, False otherwise
    """
    return username in USERS


def get_all_users():
    """
    Get a list of all valid usernames.
    
    Returns:
        list: List of valid username strings
    """
    return list(USERS.keys())
