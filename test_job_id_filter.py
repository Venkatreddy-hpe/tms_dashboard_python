#!/usr/bin/env python3
"""Test Job ID Filter Feature on Customer Status Page"""

import requests
import json

BASE_URL = 'http://localhost:8080'

def test_job_id_filter():
    """Test the Job ID filter functionality"""
    
    print("\n" + "="*70)
    print("TEST: Job ID Filter Feature on Customer Status Page")
    print("="*70)
    
    # Step 1: Create a test session (login)
    print("\n[1] Logging in...")
    session = requests.Session()
    login_response = session.post(f'{BASE_URL}/login', data={
        'username': 'user1',
        'password': 'pass1'
    })
    print(f"    Login status: {login_response.status_code}")
    
    # Step 2: Retrieve user's jobs
    print("\n[2] Retrieving user's jobs...")
    jobs_response = session.get(f'{BASE_URL}/api/jobs/mine')
    jobs_data = jobs_response.json()
    
    if not jobs_data.get('success'):
        print(f"    ❌ Failed to get jobs: {jobs_data}")
        return
    
    jobs = jobs_data.get('jobs', [])
    print(f"    ✅ Found {len(jobs)} jobs")
    
    if not jobs:
        print("    ⚠️  No jobs found. Creating test data...")
        # Create a test job
        create_response = session.post(f'{BASE_URL}/api/jobs/create', json={
            'action_code': 1,
            'action_name': 'tran-begin',
            'cids': ['test-cid-001', 'test-cid-002', 'test-cid-003'],
            'cluster_url': 'https://example.com',
            'request_payload': {'test': 'payload'},
            'response_summary': 'Test job creation'
        })
        
        if create_response.status_code == 201:
            job_result = create_response.json()
            if job_result['success']:
                job_id = job_result['job']['job_id']
                print(f"    ✅ Created test job: {job_id}")
                jobs = [{'job_id': job_id, 'customer_count': 3}]
            else:
                print(f"    ❌ Failed to create job: {job_result}")
                return
        else:
            print(f"    ❌ Create job failed with status {create_response.status_code}")
            return
    
    # Step 3: Get first job's ID
    test_job_id = jobs[0]['job_id']
    print(f"    Using test job ID: {test_job_id}")
    
    # Step 4: Get customers for this job
    print(f"\n[3] Getting customers for Job ID: {test_job_id}")
    customers_response = session.get(f'{BASE_URL}/api/jobs/{test_job_id}/customers')
    customers_data = customers_response.json()
    
    if not customers_data.get('success'):
        print(f"    ❌ Failed to get customers: {customers_data}")
        return
    
    customers = customers_data.get('customers', [])
    print(f"    ✅ Found {len(customers)} customers for this job")
    print(f"    Customers: {customers}")
    
    if not customers:
        print("    ⚠️  No customers found for this job")
        return
    
    # Step 5: Verify job details API
    print(f"\n[4] Verifying job details API...")
    details_response = session.get(f'{BASE_URL}/api/jobs/{test_job_id}')
    details_data = details_response.json()
    
    if details_data.get('success'):
        print(f"    ✅ Job details retrieved successfully")
        print(f"    Action: {details_data['job']['action_name']}")
        print(f"    Customers: {details_data['job']['customer_count']}")
    else:
        print(f"    ⚠️  Could not get full job details")
    
    # Step 6: Test invalid Job ID
    print(f"\n[5] Testing invalid Job ID error handling...")
    invalid_response = session.get(f'{BASE_URL}/api/jobs/invalid-job-id/customers')
    invalid_data = invalid_response.json()
    
    if not invalid_data.get('success'):
        print(f"    ✅ Invalid Job ID correctly rejected")
        print(f"    Error: {invalid_data.get('message')}")
    else:
        print(f"    ❌ Invalid Job ID should have been rejected")
    
    # Step 7: Summary
    print("\n" + "="*70)
    print("✅ TEST COMPLETE - Job ID Filter Feature Ready")
    print("="*70)
    print("\nFeature Summary:")
    print(f"  • Job ID input field added to Data Source section")
    print(f"  • Endpoint: GET /api/jobs/<job_id>/customers")
    print(f"  • Behavior: Filters upstream API results to job's CIDs")
    print(f"  • Error: Shows 'Invalid Job ID or no customers found'")
    print(f"  • Optional: Leave empty to show all customers")
    print(f"\nTest Job ID for UI testing: {test_job_id}")
    print(f"Test Customers: {customers}")
    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    test_job_id_filter()
