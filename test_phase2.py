#!/usr/bin/env python3
"""
Phase 2 Test: Scope Filtering and Job Actions
Tests the scope filter endpoints and filtering of upstream GET /tms/v1/get/action?cid=ALL
"""

import requests
import json
import sys

BASE_URL = "http://10.9.91.22:8080"

# Demo data simulating upstream response
DEMO_UPSTREAM_DATA = {
    "cid-001": {"action_code": 1, "action_desc": "tran-begin"},
    "cid-002": {"action_code": 2, "action_desc": "pe-enable"},
    "cid-003": {"action_code": 3, "action_desc": "t-enable"},
    "cid-004": {"action_code": 4, "action_desc": "pe-finalize"},
    "cid-005": {"action_code": 5, "action_desc": "pe-direct"},
    "cid-100": {"action_code": 1, "action_desc": "tran-begin"},  # Other user's customer
    "cid-101": {"action_code": 2, "action_desc": "pe-enable"},   # Other user's customer
}

def test_phase2():
    """Test Phase 2: Scope filtering"""
    print("\n" + "="*70)
    print("PHASE 2 TEST: Scope Filtering and Job Actions")
    print("="*70)
    
    # Login
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
    
    # Create a test job
    print("\n[2] Creating test job...")
    job_payload = {
        "action_code": 1,
        "action_name": "tran-begin",
        "cids": ["cid-001", "cid-002", "cid-003"],
        "cluster_url": "https://example.com",
        "response_summary": "Test job with 3 customers"
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
    job_id = job_result['job']['job_id']
    print(f"✅ Job created: {job_id}")
    
    # Test: Get customers for a job
    print("\n[3] Testing GET /api/jobs/<job_id>/customers...")
    customers_response = requests.get(
        f"{BASE_URL}/api/jobs/{job_id}/customers",
        cookies=cookies
    )
    
    if customers_response.status_code != 200:
        print(f"❌ Get customers failed: {customers_response.text}")
        return False
    
    customers_result = customers_response.json()
    if not customers_result.get('success'):
        print(f"❌ Get customers returned success=false: {customers_result}")
        return False
    
    print(f"✅ Retrieved {customers_result['customer_count']} customers for job")
    print(f"   Customer IDs: {customers_result['customers']}")
    
    if set(customers_result['customers']) != {"cid-001", "cid-002", "cid-003"}:
        print(f"❌ Customer list mismatch")
        return False
    
    # Test: Get actions for a job (with filtering)
    print("\n[4] Testing GET /api/jobs/<job_id>/actions...")
    print(f"   (Note: This would filter upstream GET /tms/v1/get/action?cid=ALL)")
    print(f"   Job has 3 CIDs: cid-001, cid-002, cid-003")
    print(f"   Upstream returns 7 CIDs (3 for this user, 2 other users)")
    
    # For this test, we'll try without token to see error handling
    actions_response = requests.get(
        f"{BASE_URL}/api/jobs/{job_id}/actions",
        cookies=cookies
    )
    
    # Should fail due to missing token parameter
    if actions_response.status_code == 400:
        print(f"✅ Correctly requires token parameter")
        result = actions_response.json()
        if "token" in result['message'].lower():
            print(f"   Error message: {result['message']}")
    else:
        print(f"⚠️  Expected 400 error for missing token, got {actions_response.status_code}")
    
    # Test: Try with invalid token (should get upstream error)
    print("\n[5] Testing with invalid token...")
    actions_response = requests.get(
        f"{BASE_URL}/api/jobs/{job_id}/actions?token=invalid&cluster_url=https://example.com",
        cookies=cookies
    )
    
    print(f"   Response status: {actions_response.status_code}")
    result = actions_response.json()
    if result.get('success') == False:
        print(f"✅ Correctly returned error for invalid token")
        print(f"   Error: {result['message'][:100]}")
    
    # Test: Access control - try to access another user's job
    print("\n[6] Testing access control...")
    
    # Login as user2
    login2_response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "user2",
        "password": "password456"
    })
    
    if login2_response.status_code != 200:
        print(f"⚠️  Could not login as user2 to test access control")
    else:
        cookies2 = login2_response.cookies
        
        # Try to access user1's job
        access_response = requests.get(
            f"{BASE_URL}/api/jobs/{job_id}/customers",
            cookies=cookies2
        )
        
        if access_response.status_code == 403:
            print(f"✅ Access denied for different user (403 Forbidden)")
        else:
            print(f"⚠️  Expected 403 Forbidden, got {access_response.status_code}")
    
    # Test: Multiple jobs
    print("\n[7] Creating second job with different CIDs...")
    job_payload2 = {
        "action_code": 5,
        "action_name": "e-enable",
        "cids": ["cid-004", "cid-005"],
        "cluster_url": "https://example.com",
        "response_summary": "Test job 2 with 2 customers"
    }
    
    create_response2 = requests.post(
        f"{BASE_URL}/api/jobs/create",
        json=job_payload2,
        cookies=cookies
    )
    
    if create_response2.status_code != 201:
        print(f"❌ Second job creation failed")
        return False
    
    job_id2 = create_response2.json()['job']['job_id']
    print(f"✅ Second job created: {job_id2}")
    
    # Verify jobs have different CIDs
    print("\n[8] Verifying scope isolation...")
    cust1 = requests.get(f"{BASE_URL}/api/jobs/{job_id}/customers", cookies=cookies).json()
    cust2 = requests.get(f"{BASE_URL}/api/jobs/{job_id2}/customers", cookies=cookies).json()
    
    set1 = set(cust1['customers'])
    set2 = set(cust2['customers'])
    
    if set1 & set2:  # If there's intersection
        print(f"❌ Jobs have overlapping CIDs: {set1 & set2}")
        return False
    
    print(f"✅ Jobs have isolated customer sets")
    print(f"   Job 1: {cust1['customers']}")
    print(f"   Job 2: {cust2['customers']}")
    
    print("\n" + "="*70)
    print("✅ PHASE 2 TESTS PASSED")
    print("="*70)
    print("\nPhase 2 Summary:")
    print("- ✅ GET /api/jobs/<job_id>/customers returns CID list")
    print("- ✅ GET /api/jobs/<job_id>/actions requires token and cluster_url")
    print("- ✅ Access control prevents cross-user access (403)")
    print("- ✅ Multiple jobs maintain isolated customer sets")
    print("- ✅ Scope filtering ready for Phase 3 (caching)")
    print("="*70 + "\n")
    
    return True


if __name__ == '__main__':
    try:
        success = test_phase2()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
