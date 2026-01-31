"""
Prod Customer Data Module - Handle database operations for production customer data
Stores and retrieves customer data by cluster and device_type combination
"""

import sqlite3 as _sqlite3
import json
from datetime import datetime
import os
import uuid
import math
import io
import csv
from src.db_optimizer import optimize_db_connection

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'prod_customer_data.db')

# Create wrapper for sqlite3.connect that auto-optimizes
def sqlite3_connect(path, *args, **kwargs):
    """Connect to SQLite database with automatic optimization"""
    conn = _sqlite3.connect(path, *args, **kwargs)
    return optimize_db_connection(conn, os.path.basename(path))


def normalize_customer_ids(customer_ids):
    """
    Normalize customer IDs by trimming whitespace, removing duplicates, and filtering empty values.
    
    Args:
        customer_ids: List of customer IDs
    
    Returns:
        List of normalized, unique customer IDs (strings)
    """
    if not isinstance(customer_ids, list):
        return []
    
    normalized = set()
    for cid in customer_ids:
        if isinstance(cid, str):
            trimmed = cid.strip()
            # Skip empty lines and common headers
            if trimmed and trimmed.lower() not in ['cust_id', 'customer_id', 'id']:
                normalized.add(trimmed)
    
    return sorted(list(normalized))


def parse_csv_input(csv_content):
    """
    Parse CSV content and extract customer IDs.
    Expects one customer ID per row, optionally with a header row.
    
    Args:
        csv_content: String containing CSV data
    
    Returns:
        List of extracted customer IDs
    """
    if not csv_content or not isinstance(csv_content, str):
        return []
    
    try:
        # Use csv reader to handle CSV format properly
        reader = csv.reader(io.StringIO(csv_content))
        customer_ids = []
        
        for row_idx, row in enumerate(reader):
            if not row or len(row) == 0:
                continue
            
            # First column is the customer ID
            cid = row[0].strip()
            
            # Skip header rows (case-insensitive)
            if row_idx == 0 and cid.lower() in ['cust_id', 'customer_id', 'id', 'customer']:
                continue
            
            if cid:
                customer_ids.append(cid)
        
        return normalize_customer_ids(customer_ids)
    
    except Exception as e:
        print(f"[PROD-DATA] Error parsing CSV: {e}")
        return []


def parse_manual_entry(text_input):
    """
    Parse manual text entry for customer IDs.
    Supports comma-separated or line-separated values.
    
    Args:
        text_input: String containing customer IDs (comma or line separated)
    
    Returns:
        List of extracted customer IDs
    """
    if not text_input or not isinstance(text_input, str):
        return []
    
    # Try to detect separator (comma or newline)
    comma_count = text_input.count(',')
    newline_count = text_input.count('\n')
    
    if comma_count > newline_count:
        # Comma-separated
        customer_ids = [cid.strip() for cid in text_input.split(',')]
    else:
        # Line-separated
        customer_ids = [cid.strip() for cid in text_input.split('\n')]
    
    return normalize_customer_ids(customer_ids)

def initialize_prod_customer_data_db():
    """Initialize the prod customer data database with schema"""
    conn = sqlite3_connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prod_customer_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster TEXT NOT NULL,
            device_type TEXT NOT NULL,
            data_source_url TEXT,
            total_customers INTEGER,
            total_devices INTEGER,
            customer_ids TEXT,
            created_at TEXT,
            created_by TEXT,
            updated_at TEXT,
            UNIQUE(cluster, device_type)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prod_batch_ids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT UNIQUE NOT NULL,
            cluster TEXT NOT NULL,
            device_selection TEXT NOT NULL,
            device_cap INTEGER NOT NULL,
            customers_per_batch INTEGER NOT NULL,
            total_batches INTEGER NOT NULL,
            customer_ids TEXT,
            status TEXT DEFAULT 'NEW',
            assigned_to TEXT,
            assigned_at TEXT,
            created_at TEXT,
            created_by TEXT,
            updated_at TEXT
        )
    ''')
    
    # Add total_devices column to prod_customer_data if it doesn't exist
    cursor.execute("PRAGMA table_info(prod_customer_data)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'total_devices' not in columns:
        cursor.execute('ALTER TABLE prod_customer_data ADD COLUMN total_devices INTEGER DEFAULT 0')
    
    # Add status and assigned_to columns to prod_batch_ids if they don't exist
    cursor.execute("PRAGMA table_info(prod_batch_ids)")
    batch_columns = [column[1] for column in cursor.fetchall()]
    if 'status' not in batch_columns:
        cursor.execute("ALTER TABLE prod_batch_ids ADD COLUMN status TEXT DEFAULT 'NEW'")
    if 'assigned_to' not in batch_columns:
        cursor.execute("ALTER TABLE prod_batch_ids ADD COLUMN assigned_to TEXT")
    if 'assigned_at' not in batch_columns:
        cursor.execute("ALTER TABLE prod_batch_ids ADD COLUMN assigned_at TEXT")
    if 'updated_at' not in batch_columns:
        cursor.execute("ALTER TABLE prod_batch_ids ADD COLUMN updated_at TEXT")
    if 'customers_in_batch' not in batch_columns:
        cursor.execute("ALTER TABLE prod_batch_ids ADD COLUMN customers_in_batch INTEGER DEFAULT 0")
    
    conn.commit()
    conn.close()

def save_prod_customer_data(cluster, device_type, data_source_url, customer_ids, total_devices=0, username=None):
    """
    Save or update prod customer data.
    Upserts based on (cluster, device_type) combination.
    
    Args:
        cluster: Cluster name
        device_type: Device type/selection
        data_source_url: The source URL used
        customer_ids: List of customer IDs
        total_devices: Total number of devices
        username: Username for audit trail
    
    Returns:
        dict with operation result
    """
    conn = sqlite3_connect(DB_PATH)
    cursor = conn.cursor()
    
    total_customers = len(customer_ids) if isinstance(customer_ids, list) else 0
    customer_ids_json = json.dumps(customer_ids) if isinstance(customer_ids, list) else customer_ids
    now = datetime.now().isoformat()
    
    try:
        # Check if record exists
        cursor.execute(
            'SELECT id FROM prod_customer_data WHERE cluster = ? AND device_type = ?',
            (cluster, device_type)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute('''
                UPDATE prod_customer_data 
                SET data_source_url = ?, total_customers = ?, total_devices = ?, customer_ids = ?, updated_at = ?
                WHERE cluster = ? AND device_type = ?
            ''', (data_source_url, total_customers, total_devices, customer_ids_json, now, cluster, device_type))
        else:
            # Insert new record
            cursor.execute('''
                INSERT INTO prod_customer_data 
                (cluster, device_type, data_source_url, total_customers, total_devices, customer_ids, created_at, created_by, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (cluster, device_type, data_source_url, total_customers, total_devices, customer_ids_json, now, username, now))
        
        conn.commit()
        return {'success': True, 'total_customers': total_customers, 'total_devices': total_devices}
    
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    
    finally:
        conn.close()

def get_prod_customer_data(cluster, device_type):
    """
    Retrieve prod customer data for a specific cluster and device_type.
    
    Args:
        cluster: Cluster name
        device_type: Device type/selection
    
    Returns:
        dict with customer data or None if not found
    """
    conn = sqlite3_connect(DB_PATH)
    conn.row_factory = _sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'SELECT * FROM prod_customer_data WHERE cluster = ? AND device_type = ?',
            (cluster, device_type)
        )
        row = cursor.fetchone()
        
        if row:
            # Parse customer IDs JSON
            customer_ids = json.loads(row['customer_ids']) if row['customer_ids'] else []
            return {
                'id': row['id'],
                'cluster': row['cluster'],
                'device_type': row['device_type'],
                'data_source_url': row['data_source_url'],
                'total_customers': row['total_customers'],
                'customer_ids': customer_ids,
                'created_at': row['created_at'],
                'created_by': row['created_by'],
                'updated_at': row['updated_at']
            }
        return None
    
    finally:
        conn.close()

def get_all_prod_customer_data():
    """Retrieve all prod customer data records"""
    conn = sqlite3_connect(DB_PATH)
    conn.row_factory = _sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM prod_customer_data ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            customer_ids = json.loads(row['customer_ids']) if row['customer_ids'] else []
            results.append({
                'id': row['id'],
                'cluster': row['cluster'],
                'device_type': row['device_type'],
                'data_source_url': row['data_source_url'],
                'total_customers': row['total_customers'],
                'customer_ids': customer_ids,
                'created_at': row['created_at'],
                'created_by': row['created_by'],
                'updated_at': row['updated_at']
            })
        return results
    
    finally:
        conn.close()

def delete_prod_customer_data(cluster, device_type):
    """Delete prod customer data for a specific cluster and device_type"""
    conn = sqlite3_connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'DELETE FROM prod_customer_data WHERE cluster = ? AND device_type = ?',
            (cluster, device_type)
        )
        conn.commit()
        return {'success': True}
    
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    
    finally:
        conn.close()


def generate_and_save_batches(cluster, device_selection, device_cap, customer_ids, total_customers, total_devices, username=None):
    """
    Generate batches based on device_cap and save to database.
    
    Calculation:
        - avg = total_devices / total_customers
        - customersPerBatch = floor(device_cap / avg), minimum 1
        - estimatedBatches = ceil(total_customers / customersPerBatch)
    
    Args:
        cluster: Cluster name
        device_selection: Device selection
        device_cap: User-provided device per batch cap
        customer_ids: List of customer IDs
        total_customers: Total customer count
        total_devices: Total device count
        username: Username for audit trail
    
    Returns:
        dict with success, batch_id_list, or error
    """
    if not customer_ids or len(customer_ids) == 0:
        return {'success': False, 'error': 'No customer IDs provided'}
    
    if total_customers == 0 or total_devices == 0:
        return {'success': False, 'error': 'Invalid customer or device count'}
    
    try:
        # Calculate batch parameters
        avg = total_devices / total_customers
        customers_per_batch = max(1, math.floor(device_cap / avg))
        total_batches = math.ceil(total_customers / customers_per_batch)
        
        # Split customer IDs into batches
        batches = []
        for i in range(0, len(customer_ids), customers_per_batch):
            batch_customer_ids = customer_ids[i:i + customers_per_batch]
            
            # Generate UUID-based batch ID with cluster and device suffix
            batch_uuid = str(uuid.uuid4())
            batch_id = f"{batch_uuid}_{cluster.upper()}_{device_selection.upper().replace(' ', '')}"
            
            batches.append({
                'batch_id': batch_id,
                'cluster': cluster,
                'device_selection': device_selection,
                'device_cap': device_cap,
                'customers_per_batch': customers_per_batch,
                'total_batches': total_batches,
                'customer_ids': batch_customer_ids
            })
        
        # Save batches to database
        conn = sqlite3_connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        batch_ids = []
        try:
            for batch in batches:
                cursor.execute('''
                    INSERT INTO prod_batch_ids 
                    (batch_id, cluster, device_selection, device_cap, customers_per_batch, total_batches, customer_ids, customers_in_batch, status, created_at, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    batch['batch_id'],
                    batch['cluster'],
                    batch['device_selection'],
                    batch['device_cap'],
                    batch['customers_per_batch'],
                    batch['total_batches'],
                    json.dumps(batch['customer_ids']),
                    len(batch['customer_ids']),
                    'NEW',
                    now,
                    username
                ))
                batch_ids.append(batch['batch_id'])
            
            conn.commit()
            
            return {
                'success': True,
                'batch_ids': batch_ids,
                'total_batches': len(batch_ids),
                'customers_per_batch': customers_per_batch,
                'avg_devices': round(avg, 2)
            }
        
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        
        finally:
            conn.close()
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_batches_for_cluster_device(cluster, device_selection):
    """Get all batches for a specific cluster and device selection"""
    conn = sqlite3_connect(DB_PATH)
    conn.row_factory = _sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'SELECT * FROM prod_batch_ids WHERE cluster = ? AND device_selection = ? ORDER BY created_at DESC',
            (cluster, device_selection)
        )
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            customer_ids = json.loads(row['customer_ids']) if row['customer_ids'] else []
            # Get customers_in_batch, fallback to len(customer_ids) if 0 or missing
            customers_in_batch = 0
            if 'customers_in_batch' in row.keys() and row['customers_in_batch']:
                customers_in_batch = row['customers_in_batch']
            else:
                customers_in_batch = len(customer_ids)
            
            results.append({
                'id': row['id'],
                'batch_id': row['batch_id'],
                'cluster': row['cluster'],
                'device_selection': row['device_selection'],
                'device_cap': row['device_cap'],
                'customers_per_batch': row['customers_per_batch'],
                'total_batches': row['total_batches'],
                'customer_ids': customer_ids,
                'customers_in_batch': customers_in_batch,
                'status': row['status'] if 'status' in row.keys() else 'NEW',
                'assigned_to': row['assigned_to'] if 'assigned_to' in row.keys() else None,
                'created_at': row['created_at'],
                'created_by': row['created_by']
            })
        return results
    
    finally:
        conn.close()


def get_batch_by_id(batch_id):
    """Get a batch by its batch_id and return customer_ids"""
    conn = sqlite3_connect(DB_PATH)
    conn.row_factory = _sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM prod_batch_ids WHERE batch_id = ?', (batch_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        customer_ids = json.loads(row['customer_ids']) if row['customer_ids'] else []
        return {
            'batch_id': row['batch_id'],
            'customer_ids': customer_ids,
            'customers_in_batch': row['customers_in_batch'] if 'customers_in_batch' in row.keys() else len(customer_ids)
        }
    
    finally:
        conn.close()


def delete_batch(batch_id):
    """Delete a batch by batch_id"""
    conn = sqlite3_connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM prod_batch_ids WHERE batch_id = ?', (batch_id,))
        conn.commit()
        return {'success': True}
    
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    
    finally:
        conn.close()


def delete_all_batches_for_cluster_device(cluster, device_selection):
    """Delete all batches for a specific cluster/device_selection combination"""
    conn = sqlite3_connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'DELETE FROM prod_batch_ids WHERE cluster = ? AND device_selection = ?',
            (cluster, device_selection)
        )
        deleted_count = cursor.rowcount
        conn.commit()
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} batch(es)' if deleted_count > 0 else 'No batches to delete'
        }
    
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    
    finally:
        conn.close()


def assign_batch_to_user(batch_id, username):
    """
    Atomically assign a batch to a user.
    Only assigns if batch is currently unassigned (assigned_to IS NULL).
    
    Args:
        batch_id: Batch ID to assign
        username: Username to assign to
    
    Returns:
        dict with success status. If successful, returns batch details.
        If batch already assigned, returns error message.
    """
    conn = sqlite3_connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        # Atomic update: only update if currently unassigned
        cursor.execute('''
            UPDATE prod_batch_ids 
            SET assigned_to = ?, status = ?, updated_at = ?
            WHERE batch_id = ? AND assigned_to IS NULL
        ''', (username, 'ASSIGNED', now, batch_id))
        
        conn.commit()
        
        # Check if update was successful (rowcount > 0)
        if cursor.rowcount > 0:
            # Fetch the updated batch
            cursor.execute('SELECT * FROM prod_batch_ids WHERE batch_id = ?', (batch_id,))
            row = cursor.fetchone()
            
            if row:
                return {'success': True, 'message': f'Batch assigned to {username}'}
            else:
                return {'success': False, 'error': 'Batch not found after assignment'}
        else:
            # No rows updated = batch was already assigned
            return {'success': False, 'error': 'Batch is already assigned to another user'}
    
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    
    finally:
        conn.close()


def unassign_batch(batch_id, username=None):
    """
    Unassign a batch (clear assigned_to and revert to NEW status).
    Optional: only allow unassignment if currently assigned to specified user.
    
    Args:
        batch_id: Batch ID to unassign
        username: Optional username to verify ownership before unassigning
    
    Returns:
        dict with success status
    """
    conn = sqlite3_connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        if username:
            # Only unassign if assigned to this specific user
            cursor.execute('''
                UPDATE prod_batch_ids 
                SET assigned_to = NULL, status = ?, updated_at = ?
                WHERE batch_id = ? AND assigned_to = ?
            ''', ('NEW', now, batch_id, username))
        else:
            # Unassign regardless of who it's assigned to (admin only)
            cursor.execute('''
                UPDATE prod_batch_ids 
                SET assigned_to = NULL, status = ?, updated_at = ?
                WHERE batch_id = ?
            ''', ('NEW', now, batch_id))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            return {'success': True, 'message': 'Batch unassigned'}
        else:
            return {'success': False, 'error': 'Batch not found or ownership mismatch'}
    
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    
    finally:
        conn.close()


def assign_batches_bulk(batch_ids, username):
    """
    Atomically assign multiple batches to a user.
    Only assigns batches that are currently unassigned (assigned_to IS NULL).
    Skips any batches already assigned to other users.
    
    Args:
        batch_ids: List of batch IDs to assign
        username: Username to assign to
    
    Returns:
        dict with:
            - assigned: list of successfully assigned batch IDs
            - skipped: list of dicts with {batch_id, reason}
            - message: summary message
    """
    if not batch_ids or len(batch_ids) == 0:
        return {'success': False, 'error': 'No batch IDs provided'}
    
    conn = sqlite3_connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    assigned = []
    skipped = []
    
    try:
        for batch_id in batch_ids:
            # Atomic update: only update if currently unassigned
            cursor.execute('''
                UPDATE prod_batch_ids 
                SET assigned_to = ?, status = ?, updated_at = ?
                WHERE batch_id = ? AND assigned_to IS NULL
            ''', (username, 'ASSIGNED', now, batch_id))
            
            if cursor.rowcount > 0:
                assigned.append(batch_id)
            else:
                # Check if batch exists and who it's assigned to
                cursor.execute('SELECT batch_id, assigned_to FROM prod_batch_ids WHERE batch_id = ?', (batch_id,))
                row = cursor.fetchone()
                
                if row:
                    assigned_to = row[1] if row[1] else 'unknown'
                    skipped.append({
                        'batch_id': batch_id,
                        'reason': f'Already assigned to {assigned_to}'
                    })
                else:
                    skipped.append({
                        'batch_id': batch_id,
                        'reason': 'Batch not found'
                    })
        
        conn.commit()
        
        return {
            'success': True,
            'assigned': assigned,
            'skipped': skipped,
            'message': f'Assigned {len(assigned)} batch(es)' + (f'; {len(skipped)} skipped' if skipped else '')
        }
    
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    
    finally:
        conn.close()
