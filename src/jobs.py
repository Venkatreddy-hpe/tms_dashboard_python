#!/usr/bin/env python3
"""
Job Management Module
Handles job creation, storage, and retrieval for scoped customer operations.
"""

import sqlite3 as _sqlite3
import json
import os
from datetime import datetime
import uuid
from src.db_optimizer import optimize_db_connection

# Database file location
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'jobs.db')

# Create wrapper for sqlite3.connect that auto-optimizes
def sqlite3_connect(path, *args, **kwargs):
    """Connect to SQLite database with automatic optimization"""
    conn = _sqlite3.connect(path, *args, **kwargs)
    return optimize_db_connection(conn, os.path.basename(path))

def initialize_jobs_database():
    """Initialize the jobs database schema"""
    conn = sqlite3_connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            batch_id TEXT,
            action_code INTEGER NOT NULL,
            action_name TEXT NOT NULL,
            cluster_url TEXT,
            created_at TEXT NOT NULL,
            request_payload TEXT,
            response_summary TEXT,
            status TEXT DEFAULT 'IN_PROGRESS',
            http_status INTEGER,
            error_message TEXT,
            updated_at TEXT
        )
    ''')
    
    # Create job_customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            cid TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id),
            UNIQUE(job_id, cid)
        )
    ''')
    
    # Create index for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_job_customers_job_id ON job_customers(job_id)
    ''')
    
    # Create appstatus_cache table for Phase 3 caching
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appstatus_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cid TEXT NOT NULL,
            app_name TEXT NOT NULL,
            status_data TEXT NOT NULL,
            cached_at TEXT NOT NULL,
            ttl_seconds INTEGER DEFAULT 1800,
            UNIQUE(cid, app_name)
        )
    ''')
    
    # Create index for cache lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_appstatus_cache_cid ON appstatus_cache(cid)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_appstatus_cache_cid_app ON appstatus_cache(cid, app_name)
    ''')
    
    # Schema migration: Add new columns if they don't exist
    try:
        cursor.execute('PRAGMA table_info(jobs)')
        columns = {row[1] for row in cursor.fetchall()}
        
        if 'http_status' not in columns:
            cursor.execute('ALTER TABLE jobs ADD COLUMN http_status INTEGER')
            print("[JOBS] Added http_status column to jobs table")
        
        if 'error_message' not in columns:
            cursor.execute('ALTER TABLE jobs ADD COLUMN error_message TEXT')
            print("[JOBS] Added error_message column to jobs table")
        
        if 'updated_at' not in columns:
            cursor.execute('ALTER TABLE jobs ADD COLUMN updated_at TEXT')
            print("[JOBS] Added updated_at column to jobs table")
    except Exception as e:
        print(f"[JOBS] WARNING: Schema migration error (columns may already exist): {str(e)}")
    
    conn.commit()
    conn.close()
    print("[JOBS] Database initialized successfully")


def create_job(user_id, action_code, action_name, cids, cluster_url=None, 
               batch_id=None, request_payload=None, response_summary=None, status='IN_PROGRESS'):
    """
    Create a new job and store associated customer IDs
    
    Args:
        user_id (str): ID of the user who triggered the action
        action_code (int): Code for the action (1-6)
        action_name (str): Name of the action (e.g., 'tran-begin', 'pe-enable')
        cids (list): List of customer IDs to store with this job
        cluster_url (str): Optional cluster URL
        batch_id (str): Optional batch ID
        request_payload (dict): Optional request payload
        response_summary (str): Optional response summary
        status (str): Initial job status (default: 'IN_PROGRESS')
    
    Returns:
        dict: Job details with job_id
        None: If operation fails
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Convert request_payload to JSON string if provided
        payload_str = json.dumps(request_payload) if request_payload else None
        
        conn = sqlite3_connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insert job
        cursor.execute('''
            INSERT INTO jobs 
            (job_id, user_id, batch_id, action_code, action_name, cluster_url, 
             created_at, request_payload, response_summary, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, user_id, batch_id, action_code, action_name, cluster_url,
              created_at, payload_str, response_summary, status, created_at))
        
        # Insert customer IDs for this job
        for cid in cids:
            cursor.execute('''
                INSERT INTO job_customers (job_id, cid)
                VALUES (?, ?)
            ''', (job_id, cid))
        
        conn.commit()
        conn.close()
        
        print(f"[JOBS] create_job: Successfully created job {job_id}")
        return {
            'job_id': job_id,
            'user_id': user_id,
            'action_code': action_code,
            'action_name': action_name,
            'customer_count': len(cids),
            'created_at': created_at
        }
        
    except Exception as e:
        print(f"[JOBS] ERROR in create_job: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def update_job(job_id, status, http_status=None, error_message=None, response_summary=None):
    """
    Update an existing job with status and optional error details
    
    Args:
        job_id (str): Job ID to update
        status (str): New status (SUCCESS, FAILED, IN_PROGRESS)
        http_status (int): Optional HTTP status code
        error_message (str): Optional error message
        response_summary (str): Optional updated response summary
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        updated_at = datetime.now().isoformat()
        
        conn = sqlite3_connect(DB_PATH)
        cursor = conn.cursor()
        
        # Build UPDATE query dynamically based on provided parameters
        update_fields = ['status = ?', 'updated_at = ?']
        update_values = [status, updated_at]
        
        if http_status is not None:
            update_fields.append('http_status = ?')
            update_values.append(http_status)
        
        if error_message is not None:
            update_fields.append('error_message = ?')
            update_values.append(error_message)
        
        if response_summary is not None:
            update_fields.append('response_summary = ?')
            update_values.append(response_summary)
        
        update_values.append(job_id)
        
        query = f'UPDATE jobs SET {", ".join(update_fields)} WHERE job_id = ?'
        cursor.execute(query, update_values)
        
        conn.commit()
        conn.close()
        
        print(f"[JOBS] update_job: Successfully updated job {job_id} with status={status}, http_status={http_status}")
        return True
        
    except Exception as e:
        print(f"[JOBS] ERROR in update_job: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def get_user_jobs(user_id, limit=50):
    """
    Get all jobs for a user, ordered by newest first
    
    Args:
        user_id (str): ID of the user
        limit (int): Maximum number of jobs to return
    
    Returns:
        list: List of job dictionaries with customer counts
    """
    try:
        conn = sqlite3_connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get jobs for user, ordered by newest first
        cursor.execute('''
            SELECT 
                j.job_id, j.user_id, j.action_code, j.action_name, 
                j.cluster_url, j.created_at, j.status, j.http_status, j.error_message,
                COUNT(jc.cid) as customer_count
            FROM jobs j
            LEFT JOIN job_customers jc ON j.job_id = jc.job_id
            WHERE j.user_id = ?
            GROUP BY j.job_id
            ORDER BY j.created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append({
                'job_id': row[0],
                'user_id': row[1],
                'action_code': row[2],
                'action_name': row[3],
                'cluster_url': row[4],
                'created_at': row[5],
                'status': row[6],
                'http_status': row[7],
                'error_message': row[8],
                'customer_count': row[9]
            })
        
        conn.close()
        return jobs
        
    except Exception as e:
        return []


def get_job_customers(job_id):
    """
    Get all customer IDs for a job
    
    Args:
        job_id (str): ID of the job
    
    Returns:
        list: List of customer IDs
    """
    try:
        conn = sqlite3_connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cid FROM job_customers
            WHERE job_id = ?
            ORDER BY cid
        ''', (job_id,))
        
        cids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return cids
        
    except Exception as e:
        return []


def get_job_details(job_id):
    """
    Get detailed information about a job
    
    Args:
        job_id (str): ID of the job
    
    Returns:
        dict: Job details or None if not found
    """
    try:
        conn = sqlite3_connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                j.job_id, j.user_id, j.batch_id, j.action_code, j.action_name,
                j.cluster_url, j.created_at, j.request_payload, j.response_summary, 
                j.status, COUNT(jc.cid) as customer_count
            FROM jobs j
            LEFT JOIN job_customers jc ON j.job_id = jc.job_id
            WHERE j.job_id = ?
            GROUP BY j.job_id
        ''', (job_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Parse request_payload if it exists
        payload = None
        if row[7]:
            try:
                payload = json.loads(row[7])
            except:
                payload = row[7]
        
        return {
            'job_id': row[0],
            'user_id': row[1],
            'batch_id': row[2],
            'action_code': row[3],
            'action_name': row[4],
            'cluster_url': row[5],
            'created_at': row[6],
            'request_payload': payload,
            'response_summary': row[8],
            'status': row[9],
            'customer_count': row[10]
        }
        
    except Exception as e:
        return None


# ============================================================================
# PHASE 3: APP STATUS CACHING FUNCTIONS
# ============================================================================

def get_cached_appstatus(cid, app_name='ALL', ttl_seconds=1800):
    """
    Retrieve cached app status for a CID if it exists and hasn't expired
    
    Args:
        cid (str): Customer ID
        app_name (str): App name (default 'ALL')
        ttl_seconds (int): Time-to-live in seconds (default 30 minutes)
    
    Returns:
        dict: Cached status data or None if expired/missing
    """
    try:
        conn = sqlite3_connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
            SELECT status_data, cached_at FROM appstatus_cache
            WHERE cid = ? AND app_name = ?
        ''', (cid, app_name))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        status_data_str, cached_at_str = row
        
        # Parse cached_at timestamp and check if expired
        try:
            cached_at = datetime.fromisoformat(cached_at_str)
            age_seconds = (now - cached_at).total_seconds()
            
            if age_seconds > ttl_seconds:
                # Cache expired
                return None
            
            # Cache is valid, return parsed data
            status_data = json.loads(status_data_str)
            return status_data
            
        except Exception as e:
            return None
        
    except Exception as e:
        return None


def cache_appstatus(cid, status_data, app_name='ALL', ttl_seconds=1800):
    """
    Store app status in cache
    
    Args:
        cid (str): Customer ID
        status_data (dict): Status data to cache
        app_name (str): App name (default 'ALL')
        ttl_seconds (int): Time-to-live in seconds
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        status_data_str = json.dumps(status_data)
        cached_at = datetime.now().isoformat()
        
        conn = sqlite3_connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insert or replace existing cache entry
        cursor.execute('''
            INSERT OR REPLACE INTO appstatus_cache 
            (cid, app_name, status_data, cached_at, ttl_seconds)
            VALUES (?, ?, ?, ?, ?)
        ''', (cid, app_name, status_data_str, cached_at, ttl_seconds))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        return False


def cleanup_expired_cache(ttl_seconds=1800):
    """
    Remove expired cache entries
    
    Args:
        ttl_seconds (int): Default TTL to use for cleanup
    
    Returns:
        int: Number of rows deleted
    """
    try:
        conn = sqlite3_connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Delete entries where (now - cached_at) > ttl_seconds
        cursor.execute('''
            DELETE FROM appstatus_cache
            WHERE (julianday(?) - julianday(cached_at)) * 86400 > ttl_seconds
        ''', (now,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted
        
    except Exception as e:
        return 0


def get_cached_appstatus_batch(cids, app_name='ALL', ttl_seconds=1800):
    """
    Retrieve cached app status for multiple CIDs
    Returns dict with cache hits and misses
    
    Args:
        cids (list): List of customer IDs
        app_name (str): App name (default 'ALL')
        ttl_seconds (int): Time-to-live in seconds
    
    Returns:
        dict: {
            'hits': {'cid': status_data, ...},
            'misses': ['cid1', 'cid2', ...],
            'hit_count': int,
            'miss_count': int
        }
    """
    try:
        hits = {}
        misses = []
        
        for cid in cids:
            cached = get_cached_appstatus(cid, app_name, ttl_seconds)
            if cached:
                hits[cid] = cached
            else:
                misses.append(cid)
        
        result = {
            'hits': hits,
            'misses': misses,
            'hit_count': len(hits),
            'miss_count': len(misses)
        }
        
        return result
        
    except Exception as e:
        return {
            'hits': {},
            'misses': cids,
            'hit_count': 0,
            'miss_count': len(cids)
        }


def invalidate_appstatus_cache(cid=None, app_name=None):
    """
    Invalidate cache entries
    
    Args:
        cid (str): If provided, invalidate cache for this CID only
        app_name (str): If provided, invalidate cache for this app only
    
    Returns:
        int: Number of rows deleted
    """
    try:
        conn = sqlite3_connect(DB_PATH)
        cursor = conn.cursor()
        
        if cid and app_name:
            # Invalidate specific CID+app combo
            cursor.execute('''
                DELETE FROM appstatus_cache
                WHERE cid = ? AND app_name = ?
            ''', (cid, app_name))
            deleted = cursor.rowcount
            
        elif cid:
            # Invalidate all apps for a CID
            cursor.execute('''
                DELETE FROM appstatus_cache
                WHERE cid = ?
            ''', (cid,))
            deleted = cursor.rowcount
            
        elif app_name:
            # Invalidate all CIDs for an app
            cursor.execute('''
                DELETE FROM appstatus_cache
                WHERE app_name = ?
            ''', (app_name,))
            deleted = cursor.rowcount
            
        else:
            # Clear entire cache
            cursor.execute('DELETE FROM appstatus_cache')
            deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted
        
    except Exception as e:
        return 0


def get_cache_stats():
    """
    Get cache statistics
    
    Returns:
        dict: Cache stats including total entries, hits, misses, etc.
    """
    try:
        conn = sqlite3_connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute('SELECT COUNT(*) FROM appstatus_cache')
        total = cursor.fetchone()[0]
        
        # Unique CIDs cached
        cursor.execute('SELECT COUNT(DISTINCT cid) FROM appstatus_cache')
        unique_cids = cursor.fetchone()[0]
        
        # Size in bytes (approximate)
        cursor.execute('''
            SELECT SUM(length(status_data)) FROM appstatus_cache
        ''')
        size_bytes = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_entries': total,
            'unique_cids': unique_cids,
            'size_bytes': size_bytes,
            'size_kb': round(size_bytes / 1024, 2)
        }
        
    except Exception as e:
        return {
            'total_entries': 0,
            'unique_cids': 0,
            'size_bytes': 0,
            'size_kb': 0
        }
