#!/usr/bin/env python3
"""
Load sample audit data for testing TMS Dashboard features
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.audit_db import initialize_database, log_action
from datetime import datetime, timedelta
import random

# Sample customer IDs from the demo data
CUSTOMER_IDS = [
    "685102e6fc1511ef9ee8561b853a244c",
    "6866cf36c19511f0a69e0a3464f46ecd",
    "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d",
    "8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e",
    "9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f"
]

USERS = ["admin", "user1", "user2", "analyst", "manager"]

ACTION_TYPES = ["Trans-Begin", "PE-Enable", "T-Enable", "PE-Finalize", "Login", "Logout"]

IP_ADDRESSES = ["127.0.0.1", "10.9.91.22", "10.9.91.45", "10.9.91.67", "192.168.1.100"]

def create_sample_data():
    """Create sample audit trail data"""
    print("=" * 60)
    print("Loading Sample Audit Data")
    print("=" * 60)
    
    # Initialize database
    print("\n📊 Initializing database...")
    initialize_database()
    print("✅ Database initialized")
    
    # Create sample audit entries for the past 7 days
    now = datetime.now()
    entries_created = 0
    
    print("\n📝 Creating sample audit entries...")
    
    # Generate 50 sample audit entries
    for i in range(50):
        # Random time in the past 7 days
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        
        timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        user_id = random.choice(USERS)
        action_type = random.choice(ACTION_TYPES)
        customer_id = random.choice(CUSTOMER_IDS) if action_type not in ["Login", "Logout"] else None
        ip_address = random.choice(IP_ADDRESSES)
        
        # 90% success rate
        status = "success" if random.random() < 0.9 else "failure"
        error_message = None
        
        if status == "failure":
            error_messages = [
                "Connection timeout",
                "Authentication failed",
                "Invalid customer ID",
                "Service unavailable",
                "Permission denied",
                "Rate limit exceeded"
            ]
            error_message = random.choice(error_messages)
        
        # Random duration between 50ms and 2000ms
        duration_ms = random.randint(50, 2000)
        
        # Create the audit entry with custom timestamp
        # We need to insert directly since log_action uses CURRENT_TIMESTAMP
        from src.audit_db import get_db_connection
        import json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        customer_ids_str = json.dumps([customer_id]) if customer_id else None
        
        cursor.execute('''
            INSERT INTO audit_log 
            (user_id, action_type, customer_ids, timestamp, ip_address, status, error_message, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, action_type, customer_ids_str, timestamp.isoformat(), ip_address, status, error_message, duration_ms))
        
        conn.commit()
        conn.close()
        
        entries_created += 1
        
        if entries_created % 10 == 0:
            print(f"  ✓ Created {entries_created} entries...")
    
    print(f"\n✅ Successfully created {entries_created} sample audit entries")
    
    # Create some specific scenarios for each customer
    print("\n📋 Creating customer-specific scenarios...")
    
    for customer_id in CUSTOMER_IDS:
        # Create a sequence of actions for this customer
        base_time = now - timedelta(hours=random.randint(1, 48))
        
        actions_sequence = [
            ("Trans-Begin", "admin", "success", None, 150),
            ("PE-Enable", "admin", "success", None, 450),
            ("T-Enable", "user1", "success", None, 320),
            ("PE-Finalize", "user1", "success", None, 280),
        ]
        
        for idx, (action, user, status, error, duration) in enumerate(actions_sequence):
            action_time = base_time + timedelta(minutes=idx * 5)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_log 
                (user_id, action_type, customer_ids, timestamp, ip_address, status, error_message, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user, action, customer_id, action_time.isoformat(), "127.0.0.1", status, error, duration))
            
            conn.commit()
            conn.close()
            
            entries_created += 1
    
    print(f"  ✓ Added workflow sequences for {len(CUSTOMER_IDS)} customers")
    
    # Add some failures for testing
    print("\n⚠️  Adding some failure scenarios...")
    
    failure_scenarios = [
        ("685102e6fc1511ef9ee8561b853a244c", "PE-Enable", "analyst", "Connection timeout after 30s", 30000),
        ("6866cf36c19511f0a69e0a3464f46ecd", "T-Enable", "manager", "Invalid credentials provided", 120),
        ("7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d", "Trans-Begin", "user2", "Rate limit exceeded - try again later", 85),
    ]
    
    for customer_id, action, user, error, duration in failure_scenarios:
        failure_time = now - timedelta(hours=random.randint(1, 24))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_log 
            (user_id, action_type, customer_ids, timestamp, ip_address, status, error_message, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user, action, customer_id, failure_time.isoformat(), "10.9.91.22", "failure", error, duration))
        
        conn.commit()
        conn.close()
        
        entries_created += 1
    
    print(f"  ✓ Added {len(failure_scenarios)} failure scenarios")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Sample Data Summary")
    print("=" * 60)
    
    from src.audit_db import get_audit_stats
    stats = get_audit_stats()
    
    print(f"Total Records:      {stats.get('total_records', 0)}")
    print(f"Unique Users:       {stats.get('unique_users', 0)}")
    print(f"Unique Actions:     {stats.get('unique_actions', 0)}")
    print(f"Successful:         {stats.get('successful_actions', 0)}")
    print(f"Failed:             {stats.get('failed_actions', 0)}")
    print(f"Success Rate:       {stats.get('success_rate_percent', 0)}%")
    
    print("\n✅ Sample data loaded successfully!")
    print("\n💡 You can now:")
    print("   1. Login at http://localhost:8080/login (admin/password123)")
    print("   2. Click any Customer ID to see audit history")
    print("   3. View full audit trail at /api/audit/trail")
    print("   4. Check customer-specific history by clicking customer IDs")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    try:
        create_sample_data()
    except Exception as e:
        print(f"\n❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
