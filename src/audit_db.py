"""
Audit Database Module for TMS Dashboard.
Manages SQLite database operations for audit logging.
"""

import sqlite3
import os
from datetime import datetime
import json
from src.db_optimizer import optimize_db_connection

# Database configuration
AUDIT_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'audit.db')


def get_db_connection():
    """
    Get a connection to the audit database.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(AUDIT_DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    conn = optimize_db_connection(conn, 'audit.db')
    return conn


def initialize_database():
    """
    Initialize the audit database with tables and indexes.
    Creates tables if they don't exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create audit_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            customer_ids TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            status TEXT,
            error_message TEXT,
            duration_ms INTEGER
        )
    ''')
    
    # Create indexes for optimized queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_timestamp 
        ON audit_log(user_id, timestamp DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_action_type 
        ON audit_log(action_type)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON audit_log(timestamp DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_customer_search 
        ON audit_log(customer_ids)
    ''')
    
    conn.commit()
    conn.close()
    
    return True


def log_action(user_id, action_type, customer_ids=None, ip_address=None, 
               status='success', error_message=None, duration_ms=None):
    """
    Log a user action to the audit database.
    
    Args:
        user_id (str): Username who performed the action
        action_type (str): Type of action (Trans-Begin, PE-Enable, etc.)
        customer_ids (list or str): Customer ID(s) affected
        ip_address (str): Source IP address
        status (str): 'success' or 'failure'
        error_message (str): Error message if failed
        duration_ms (int): Duration of action in milliseconds
    
    Returns:
        int: ID of the logged action or None if failed
    """
    try:
        # Convert customer_ids to JSON string if it's a list
        if isinstance(customer_ids, list):
            customer_ids_str = json.dumps(customer_ids)
        else:
            customer_ids_str = customer_ids
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_log 
            (user_id, action_type, customer_ids, ip_address, status, error_message, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, action_type, customer_ids_str, ip_address, status, error_message, duration_ms))
        
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        
        return log_id
    
    except Exception as e:
        print(f"Error logging action: {str(e)}")
        return None


def get_audit_trail(limit=50, user_id=None, action_type=None, customer_id=None):
    """
    Retrieve audit trail records from the database.
    
    Args:
        limit (int): Maximum number of records to return
        user_id (str): Filter by user (optional)
        action_type (str): Filter by action type (optional)
        customer_id (str): Filter by customer ID (optional)
    
    Returns:
        list: List of audit log records (dicts)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM audit_log WHERE 1=1'
        params = []
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        if action_type:
            query += ' AND action_type = ?'
            params.append(action_type)
        
        if customer_id:
            query += ' AND customer_ids LIKE ?'
            params.append(f'%{customer_id}%')
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to dictionaries
        records = []
        for row in rows:
            record = dict(row)
            # Parse customer_ids JSON if present
            if record['customer_ids']:
                try:
                    record['customer_ids'] = json.loads(record['customer_ids'])
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, keep as string
                    pass
            records.append(record)
        
        return records
    
    except Exception as e:
        print(f"Error retrieving audit trail: {str(e)}")
        return []


def get_user_actions(user_id, limit=50):
    """
    Get all actions performed by a specific user.
    
    Args:
        user_id (str): Username to query
        limit (int): Maximum number of records to return
    
    Returns:
        list: List of audit log records for the user
    """
    return get_audit_trail(limit=limit, user_id=user_id)


def get_customer_actions(customer_id, limit=50):
    """
    Get all actions related to a specific customer.
    
    Args:
        customer_id (str): Customer ID to query
        limit (int): Maximum number of records to return
    
    Returns:
        list: List of audit log records for the customer
    """
    return get_audit_trail(limit=limit, customer_id=customer_id)


def get_action_types():
    """
    Get a list of all action types that have been logged.
    
    Returns:
        list: List of unique action type strings
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT action_type FROM audit_log ORDER BY action_type')
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"Error getting action types: {str(e)}")
        return []


def get_audit_stats():
    """
    Get statistics about audit logs.
    
    Returns:
        dict: Statistics including total records, unique users, action types, etc.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total records
        cursor.execute('SELECT COUNT(*) as total FROM audit_log')
        total = cursor.fetchone()[0]
        
        # Total users
        cursor.execute('SELECT COUNT(DISTINCT user_id) as users FROM audit_log')
        users = cursor.fetchone()[0]
        
        # Total actions
        cursor.execute('SELECT COUNT(DISTINCT action_type) as actions FROM audit_log')
        actions = cursor.fetchone()[0]
        
        # Success rate
        cursor.execute('SELECT COUNT(*) as success FROM audit_log WHERE status = "success"')
        successes = cursor.fetchone()[0]
        
        success_rate = (successes / total * 100) if total > 0 else 0
        
        conn.close()
        
        return {
            'total_records': total,
            'unique_users': users,
            'unique_actions': actions,
            'successful_actions': successes,
            'failed_actions': total - successes,
            'success_rate_percent': round(success_rate, 2)
        }
    
    except Exception as e:
        print(f"Error getting audit stats: {str(e)}")
        return {}


def clear_audit_logs():
    """
    Clear all audit logs from the database.
    WARNING: This is a destructive operation and should be used with caution.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM audit_log')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clearing audit logs: {str(e)}")
        return False
