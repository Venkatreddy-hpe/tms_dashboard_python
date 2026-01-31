#!/usr/bin/env python3
"""
Test script to verify the Set Action duplicate job creation fix
Tests that only ONE job record is created per Set Action request
"""

import sqlite3
import json
from datetime import datetime, timedelta
import sys

def count_recent_jobs(database_path, minutes=1):
    """Count jobs created in the last N minutes"""
    try:
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get recent jobs (last N minutes)
        time_threshold = datetime.now() - timedelta(minutes=minutes)
        query = """
            SELECT job_id, user_id, action_code, action_name, created_at, status
            FROM jobs
            WHERE created_at > ?
            ORDER BY created_at DESC
        """
        cursor.execute(query, (time_threshold.isoformat(),))
        jobs = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in jobs]
    except Exception as e:
        print(f"ERROR: Failed to query jobs database: {e}")
        return []

def analyze_duplicate_jobs(jobs):
    """Analyze job list to find duplicates (same action, timestamp within seconds)"""
    if len(jobs) < 2:
        return {"status": "OK", "message": f"Only {len(jobs)} job(s) found - no duplicates"}
    
    # Group by action and look for same-timestamp jobs
    duplicates = []
    analyzed = set()
    
    for i, job1 in enumerate(jobs):
        if i in analyzed:
            continue
        for j, job2 in enumerate(jobs[i+1:], i+1):
            if j in analyzed:
                continue
            
            # Check if same action and created within 2 seconds
            if (job1['action_code'] == job2['action_code'] and
                job1['action_name'] == job2['action_name']):
                
                time1 = datetime.fromisoformat(job1['created_at'])
                time2 = datetime.fromisoformat(job2['created_at'])
                time_diff = abs((time1 - time2).total_seconds())
                
                if time_diff < 2:  # Within 2 seconds = likely duplicate
                    duplicates.append({
                        "job1_id": job1['job_id'],
                        "job2_id": job2['job_id'],
                        "action": job1['action_name'],
                        "time_diff_seconds": time_diff
                    })
                    analyzed.add(i)
                    analyzed.add(j)
    
    if duplicates:
        return {
            "status": "DUPLICATE FOUND",
            "count": len(duplicates),
            "duplicates": duplicates
        }
    else:
        return {"status": "OK", "message": "No duplicate jobs found"}

def main():
    print("\n" + "="*70)
    print("  Set Action Duplicate Job Fix Test")
    print("="*70)
    
    db_path = '/home/pdanekula/tms_dashboard_python/src/jobs.db'
    
    # Get recent jobs
    print("\n📋 Fetching recent jobs (last 5 minutes)...")
    recent_jobs = count_recent_jobs(db_path, minutes=5)
    
    if not recent_jobs:
        print("❌ No recent jobs found in database")
        print("   Tip: Run a Set Action in the UI first, then run this test again")
        return False
    
    print(f"✅ Found {len(recent_jobs)} recent job record(s)\n")
    
    # Display jobs
    print("Job Records:")
    print("-" * 70)
    for idx, job in enumerate(recent_jobs, 1):
        print(f"{idx}. Job ID: {job['job_id']}")
        print(f"   Action: {job['action_name']} (code: {job['action_code']})")
        print(f"   User: {job['user_id']}")
        print(f"   Created: {job['created_at']}")
        print(f"   Status: {job['status']}")
        print()
    
    # Analyze for duplicates
    print("\n🔍 Analyzing for duplicate jobs...")
    print("-" * 70)
    analysis = analyze_duplicate_jobs(recent_jobs)
    
    if analysis['status'] == 'OK':
        print(f"✅ PASS: {analysis['message']}")
        return True
    else:
        print(f"❌ FAIL: {analysis['status']}")
        if 'count' in analysis:
            print(f"   Found {analysis['count']} duplicate(s):")
            for dup in analysis['duplicates']:
                print(f"   - {dup['job1_id']}")
                print(f"     {dup['job2_id']}")
                print(f"     Action: {dup['action']}")
                print(f"     Time difference: {dup['time_diff_seconds']:.2f} seconds")
        return False

if __name__ == '__main__':
    success = main()
    print("\n" + "="*70)
    sys.exit(0 if success else 1)
