#!/usr/bin/env python3
"""
Phase 1 Test: Job Creation and Retrieval
Tests the /api/jobs/create and /api/jobs/mine endpoints
"""

import requests
import json
import sys

BASE_URL = "http://10.9.91.22:8080"

def test_phase1():
    """Test Phase 1: Job creation and retrieval"""
    print("\n" + "="*70)
    print("PHASE 1 TEST: Job Creation and Retrieval")
    print("="*70)
    
    # First, login with a test user
    print("\n[1] Testing login...")
    login_response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "user1",
        "password": "password123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    print("✅ Login successful")
    cookies = login_response.cookies
    
    # Test creating a job
    print("\n[2] Testing job creation (/api/jobs/create)...")
    job_payload = {
        "action_code": 1,
        "action_name": "tran-begin",
        "cids": ["cid-001", "cid-002", "cid-003"],
        "cluster_url": "https://example.com",
        "request_payload": {
            "action": "tran-begin",
            "cids": ["cid-001", "cid-002", "cid-003"]
        },
        "response_summary": "Successfully processed 3 customers"
    }
    
    create_response = requests.post(
        f"{BASE_URL}/api/jobs/create",
        json=job_payload,
        cookies=cookies
    )
    
    if create_response.status_code != 201:
        print(f"❌ Job creation failed: {create_response.text}")
        return False
    
    job_result = create_response.json()
    if not job_result.get('success'):
        print(f"❌ Job creation returned success=false: {job_result}")
        return False
    
    job_id = job_result['job']['job_id']
    print(f"✅ Job created successfully")
    print(f"   Job ID: {job_id}")
    print(f"   Customer Count: {job_result['job']['customer_count']}")
    print(f"   Action: {job_result['job']['action_name']} (code: {job_result['job']['action_code']})")
    
    # Test retrieving user's jobs
    print("\n[3] Testing job retrieval (/api/jobs/mine)...")
    list_response = requests.get(
        f"{BASE_URL}/api/jobs/mine",
        cookies=cookies
    )
    
    if list_response.status_code != 200:
        print(f"❌ Job retrieval failed: {list_response.text}")
        return False
    
    list_result = list_response.json()
    if not list_result.get('success'):
        print(f"❌ Job retrieval returned success=false: {list_result}")
        return False
    
    print(f"✅ Job retrieval successful")
    print(f"   Jobs found: {list_result['job_count']}")
    
    if list_result['job_count'] > 0:
        latest_job = list_result['jobs'][0]
        print(f"\n   Latest Job:")
        print(f"     Job ID: {latest_job['job_id']}")
        print(f"     Action: {latest_job['action_name']} (code: {latest_job['action_code']})")
        print(f"     Customer Count: {latest_job['customer_count']}")
        print(f"     Created: {latest_job['created_at']}")
        print(f"     Status: {latest_job['status']}")
        
        if latest_job['job_id'] == job_id:
            print(f"\n✅ Job created matches latest job retrieved!")
        else:
            print(f"\n⚠️  Job IDs don't match (expected: {job_id}, got: {latest_job['job_id']})")
    else:
        print(f"⚠️  No jobs found for user")
    
    # Test creating another job with different action
    print("\n[4] Creating second job with different action...")
    job_payload2 = {
        "action_code": 5,
        "action_name": "pe-direct",
        "cids": ["cid-004", "cid-005"],
        "cluster_url": "https://example.com",
        "response_summary": "Successfully processed 2 customers"
    }
    
    create_response2 = requests.post(
        f"{BASE_URL}/api/jobs/create",
        json=job_payload2,
        cookies=cookies
    )
    
    if create_response2.status_code != 201:
        print(f"❌ Second job creation failed: {create_response2.text}")
        return False
    
    job_id2 = create_response2.json()['job']['job_id']
    print(f"✅ Second job created: {job_id2}")
    
    # Verify both jobs are listed
    print("\n[5] Verifying both jobs in list...")
    list_response2 = requests.get(
        f"{BASE_URL}/api/jobs/mine",
        cookies=cookies
    )
    
    jobs_list = list_response2.json()['jobs']
    job_ids = [j['job_id'] for j in jobs_list]
    
    if job_id in job_ids and job_id2 in job_ids:
        print(f"✅ Both jobs found in list")
        print(f"   Total jobs: {list_response2.json()['job_count']}")
    else:
        print(f"❌ Not all jobs found in list")
        return False
    
    print("\n" + "="*70)
    print("✅ PHASE 1 TESTS PASSED")
    print("="*70 + "\n")
    return True


if __name__ == '__main__':
    try:
        success = test_phase1()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
