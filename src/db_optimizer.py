"""
SQLite Database Optimizer
Applies performance optimizations to SQLite database connections.
Safe to apply - no data loss, only performance improvements.
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)


def optimize_db_connection(conn, db_name="database"):
    """
    Apply SQLite performance optimizations to a database connection.
    
    These optimizations are safe and include:
    - Memory cache: 500 MB (-500 pages = ~500 MB)
    - MMAP: 500 MB for faster reads
    - Journal mode: WAL (Write-Ahead Logging) for better concurrency
    - Synchronous: NORMAL (safer than FULL, faster than FULL)
    - Temp store: MEMORY for faster temp operations
    
    Args:
        conn (sqlite3.Connection): Database connection
        db_name (str): Database name for logging
    
    Returns:
        sqlite3.Connection: Optimized connection
    """
    try:
        cursor = conn.cursor()
        
        # 1. Set cache size to 500 MB (negative value = MB, positive = pages)
        cursor.execute('PRAGMA cache_size = -500')
        
        # 2. Enable memory-mapped I/O (500 MB)
        # 524288000 bytes = 500 MB
        cursor.execute('PRAGMA mmap_size = 524288000')
        
        # 3. Set journal mode to WAL (Write-Ahead Logging)
        # Better for concurrent access and performance
        cursor.execute('PRAGMA journal_mode = WAL')
        
        # 4. Set synchronous to NORMAL (level 1)
        # Faster than FULL (level 2), safe enough for most apps
        # Still syncs at critical points
        cursor.execute('PRAGMA synchronous = NORMAL')
        
        # 5. Set temp_store to MEMORY
        # Temp tables stored in memory instead of disk
        cursor.execute('PRAGMA temp_store = MEMORY')
        
        # 6. Enable foreign keys
        cursor.execute('PRAGMA foreign_keys = ON')
        
        # 7. Set busy timeout to 5 seconds
        conn.execute('PRAGMA busy_timeout = 5000')
        
        conn.commit()
        
        logger.info(f"SQLite optimizations applied to {db_name}")
        logger.debug(f"  - Cache: 500 MB")
        logger.debug(f"  - MMAP: 500 MB")
        logger.debug(f"  - Journal: WAL")
        logger.debug(f"  - Synchronous: NORMAL")
        
        return conn
        
    except Exception as e:
        logger.error(f"Error applying SQLite optimizations to {db_name}: {e}")
        # Return connection anyway, optimization is optional
        return conn


class OptimizedConnection:
    """
    Wrapper class that automatically applies optimizations to any SQLite connection.
    Usage: Replace sqlite3.connect() calls with OptimizedConnection()
    
    Example:
        conn = OptimizedConnection('mydb.db')  # Instead of sqlite3.connect('mydb.db')
    """
    
    def __new__(cls, db_path, *args, **kwargs):
        """Create and optimize a SQLite connection"""
        conn = sqlite3.connect(db_path, *args, **kwargs)
        db_name = db_path.split('/')[-1] if '/' in db_path else db_path
        return optimize_db_connection(conn, db_name)


def apply_optimizations_to_all_dbs():
    """
    Helper function to test optimization on all databases.
    Can be called separately for batch optimization.
    """
    import os
    
    db_files = [
        os.path.join(os.path.dirname(__file__), '..', 'prod_customer_data.db'),
        os.path.join(os.path.dirname(__file__), '..', 'jobs.db'),
        os.path.join(os.path.dirname(__file__), '..', 'audit.db'),
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                optimize_db_connection(conn, os.path.basename(db_file))
                conn.close()
                print(f"✓ Optimized {os.path.basename(db_file)}")
            except Exception as e:
                print(f"✗ Failed to optimize {os.path.basename(db_file)}: {e}")
        else:
            print(f"- {os.path.basename(db_file)} not found yet")

