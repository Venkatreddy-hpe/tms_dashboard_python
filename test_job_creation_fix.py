#!/usr/bin/env python3
"""
Test script to verify job creation fix for Set Action
Tests that jobs are properly created and committed to jobs.db
"""

import sys
import os
import sqlite3
import json
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, os.path.dirname(__file__))

from src.jobs import initialize_jobs_database, create_job, get_user_jobs, DB_PATH

def test_job_creation():
    """Test that jobs are created and persisted correctly"""
    
    print("\n" + "="*70)
    print("TEST: Job Creation with SQLite Optimizer")
    print("="*70)
    
    # 0. Clean up old database (for fresh test)
    print("\n0. Cleaning up old database...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"   ✓ Removed old database")
    
    # 1. Initialize database
    print("\n1. Initializing jobs database...")
    initialize_jobs_database()
    print(f"   ✓ Database initialized at: {DB_PATH}")
    
    # 2. Check if DB file exists
    if not os.path.exists(DB_PATH):
        print(f"   ✗ ERROR: Database file not found at {DB_PATH}")
        return False
    print(f"   ✓ Database file exists: {os.path.getsize(DB_PATH)} bytes")
    
    # 3. Create a test job
    print("\n3. Creating test job...")
    test_user_id = "test_user_001"
    test_cids = ["cid_001", "cid_002", "cid_003"]
    test_action_code = 1
    test_action_name = "tran-begin"
    
    job = create_job(
        user_id=test_user_id,
        action_code=test_action_code,
        action_name=test_action_name,
        cids=test_cids,
        cluster_url="https://api.example.com",
        request_payload={"action": "Trans-Begin", "cids": test_cids},
        response_summary='{"success": true, "message": "Action completed"}'
    )
    
    if not job:
        print("   ✗ ERROR: create_job returned None")
        return False
    
    print(f"   ✓ Job created: {job['job_id']}")
    print(f"   ✓ Action code: {job['action_code']}")
    print(f"   ✓ Customer count: {job['customer_count']}")
    
    # 4. Verify job was persisted to database
    print("\n4. Verifying job in database...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check jobs table
        cursor.execute("SELECT job_id, user_id, action_code, action_name FROM jobs WHERE job_id = ?", 
                      (job['job_id'],))
        row = cursor.fetchone()
        
        if not row:
            print(f"   ✗ ERROR: Job not found in jobs table")
            conn.close()
            return False
        
        print(f"   ✓ Found in jobs table:")
        print(f"     - job_id: {row[0]}")
        print(f"     - user_id: {row[1]}")
        print(f"     - action_code: {row[2]}")
        print(f"     - action_name: {row[3]}")
        
        # Check job_customers table
        cursor.execute("SELECT cid FROM job_customers WHERE job_id = ? ORDER BY cid", 
                      (job['job_id'],))
        cids_in_db = [r[0] for r in cursor.fetchall()]
        
        if cids_in_db != sorted(test_cids):
            print(f"   ✗ ERROR: Customer IDs mismatch")
            print(f"     Expected: {sorted(test_cids)}")
            print(f"     Got: {cids_in_db}")
            conn.close()
            return False
        
        print(f"   ✓ Found in job_customers table:")
        for cid in cids_in_db:
            print(f"     - {cid}")
        
        conn.close()
    except Exception as e:
        print(f"   ✗ ERROR: Database query failed: {str(e)}")
        return False
    
    # 5. Verify get_user_jobs retrieves the job
    print("\n5. Verifying get_user_jobs retrieval...")
    jobs = get_user_jobs(test_user_id, limit=10)
    
    if not jobs:
        print(f"   ✗ ERROR: get_user_jobs returned empty list")
        return False
    
    found = False
    for retrieved_job in jobs:
        if retrieved_job['job_id'] == job['job_id']:
            found = True
            print(f"   ✓ Job retrieved from get_user_jobs")
            print(f"     - job_id: {retrieved_job['job_id']}")
            print(f"     - action_name: {retrieved_job['action_name']}")
            print(f"     - customer_count: {retrieved_job['customer_count']}")
            break
    
    if not found:
        print(f"   ✗ ERROR: Job not found in get_user_jobs results")
        return False
    
    # 6. Create multiple jobs to test scalability
    print("\n6. Creating 5 additional jobs for scalability test...")
    for i in range(5):
        test_job = create_job(
            user_id=test_user_id,
            action_code=(i % 5) + 1,
            action_name=f"action_{i}",
            cids=[f"cid_{i}"],
            response_summary='{"success": true}'
        )
        if test_job:
            print(f"   ✓ Job {i+1}: {test_job['job_id'][:8]}...")
        else:
            print(f"   ✗ Job {i+1} creation failed")
            return False
    
    # 7. Verify all jobs are in database
    print("\n7. Verifying all jobs in database...")
    all_jobs = get_user_jobs(test_user_id, limit=50)
    print(f"   ✓ Total jobs for user: {len(all_jobs)}")
    if len(all_jobs) != 6:
        print(f"   ✗ ERROR: Expected 6 jobs, found {len(all_jobs)}")
        return False
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)
    print("\nConclusion:")
    print("- Jobs are being created successfully")
    print("- Jobs are persisted to jobs.db with proper commit()")
    print("- Customer IDs are correctly associated with jobs")
    print("- SQLite optimizer doesn't break job creation")
    print("- get_user_jobs retrieves jobs correctly")
    print("\n")
    
    return True

if __name__ == '__main__':
    success = test_job_creation()
    sys.exit(0 if success else 1)
