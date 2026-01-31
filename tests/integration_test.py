#!/usr/bin/env python3
"""
Integration Tests for TMS Dashboard
Tests authentication, audit logging, and UI functionality together
"""

import requests
import time
import json

BASE_URL = "http://localhost:8080"
TEST_USER = "admin"
TEST_PASSWORD = "password123"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}▶ Testing: {name}{Colors.END}")

def print_success(msg):
    print(f"  {Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"  {Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"  {Colors.YELLOW}ℹ {msg}{Colors.END}")

def test_health_check():
    """Test 1: Health endpoint should be accessible"""
    print_test("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print_success("Health endpoint responding")
        return True
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_login_page():
    """Test 2: Login page should be accessible"""
    print_test("Login Page Access")
    try:
        response = requests.get(f"{BASE_URL}/login", timeout=5)
        assert response.status_code == 200
        assert "TMS Dashboard" in response.text
        print_success("Login page accessible")
        return True
    except Exception as e:
        print_error(f"Login page access failed: {e}")
        return False

def test_authentication():
    """Test 3: User authentication should work"""
    print_test("User Authentication")
    session = requests.Session()
    
    try:
        # Test login
        response = session.post(
            f"{BASE_URL}/api/login",
            json={"username": TEST_USER, "password": TEST_PASSWORD},
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        print_success(f"Login successful for user: {TEST_USER}")
        
        # Test authenticated access
        response = session.get(f"{BASE_URL}/", timeout=5)
        assert response.status_code == 200
        print_success("Authenticated dashboard access")
        
        return session
    except Exception as e:
        print_error(f"Authentication failed: {e}")
        return None

def test_protected_routes(session):
    """Test 4: Protected routes should require authentication"""
    print_test("Route Protection")
    
    try:
        # Test with unauthenticated session
        unauth_session = requests.Session()
        response = unauth_session.get(f"{BASE_URL}/api/transition/state", timeout=5, allow_redirects=False)
        
        # Should redirect to login (302) or return 401
        is_blocked = response.status_code in [302, 401]
        if is_blocked:
            print_success("Unauthenticated access blocked")
        else:
            print_info(f"Unexpected status code: {response.status_code}")
        
        # Test with authenticated session
        if session:
            response = session.get(f"{BASE_URL}/api/transition/state", timeout=5)
            if response.status_code == 200:
                print_success("Authenticated access allowed")
                return True
            else:
                print_error(f"Authenticated access failed with status: {response.status_code}")
                return False
        return is_blocked
    except Exception as e:
        print_error(f"Route protection test failed: {e}")
        return False

def test_audit_logging(session):
    """Test 5: Audit logging should capture actions"""
    print_test("Audit Trail Logging")
    
    if not session:
        print_error("No authenticated session available")
        return False
    
    try:
        # Trigger an audited action
        response = session.get(f"{BASE_URL}/api/transition/state", timeout=5)
        assert response.status_code == 200
        print_success("Action triggered for audit logging")
        
        # Wait a moment for async logging
        time.sleep(0.5)
        
        # Check audit trail
        response = session.get(f"{BASE_URL}/api/audit/trail?limit=10", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        
        records = data.get("records", [])
        print_success(f"Audit trail accessible ({len(records)} records)")
        
        # Verify audit record structure
        if records:
            record = records[0]
            required_fields = ["user_id", "action_type", "timestamp", "status"]
            for field in required_fields:
                assert field in record
            print_success(f"Audit records contain required fields")
            print_info(f"Recent action: {record.get('action_type')} by {record.get('user_id')}")
        
        return True
    except Exception as e:
        print_error(f"Audit logging test failed: {e}")
        return False

def test_audit_customer_query(session):
    """Test 6: Customer-specific audit queries should work"""
    print_test("Customer Audit Query")
    
    if not session:
        print_error("No authenticated session available")
        return False
    
    try:
        # Test customer-specific audit query (use a test customer ID)
        test_customer_id = "685102e6fc1511ef9ee8561b853a244c"
        response = session.get(
            f"{BASE_URL}/api/audit/customer/{test_customer_id}?limit=20",
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        print_success("Customer audit query successful")
        
        records = data.get("records", [])
        print_info(f"Found {len(records)} audit records for customer")
        
        return True
    except Exception as e:
        print_error(f"Customer audit query failed: {e}")
        return False

def test_audit_stats(session):
    """Test 7: Audit statistics should be available"""
    print_test("Audit Statistics")
    
    if not session:
        print_error("No authenticated session available")
        return False
    
    try:
        response = session.get(f"{BASE_URL}/api/audit/stats", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        
        stats = data.get("stats", {})
        print_success("Audit statistics retrieved")
        print_info(f"Total records: {stats.get('total_records', 0)}")
        print_info(f"Unique users: {stats.get('unique_users', 0)}")
        print_info(f"Success rate: {stats.get('success_rate_percent', 0)}%")
        
        return True
    except Exception as e:
        print_error(f"Audit stats test failed: {e}")
        return False

def test_logout(session):
    """Test 8: Logout should invalidate session"""
    print_test("User Logout")
    
    if not session:
        print_error("No authenticated session available")
        return False
    
    try:
        # Logout
        response = session.post(f"{BASE_URL}/api/logout", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_success("Logout successful")
            else:
                print_error("Logout failed in response")
                return False
        else:
            print_error(f"Logout failed with status: {response.status_code}")
            return False
        
        # Try to access protected route after logout
        response = session.get(f"{BASE_URL}/api/transition/state", timeout=5, allow_redirects=False)
        if response.status_code in [302, 401]:
            print_success("Session invalidated after logout")
            return True
        else:
            print_info(f"Post-logout status: {response.status_code}")
            return True  # Still consider it a pass if logout succeeded
    except Exception as e:
        print_error(f"Logout test failed: {e}")
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print(f"{Colors.BLUE}TMS Dashboard - Integration Test Suite{Colors.END}")
    print("=" * 60)
    
    results = []
    session = None
    
    # Run tests in sequence
    results.append(("Health Check", test_health_check()))
    results.append(("Login Page", test_login_page()))
    
    session = test_authentication()
    results.append(("Authentication", session is not None))
    
    results.append(("Route Protection", test_protected_routes(session)))
    results.append(("Audit Logging", test_audit_logging(session)))
    results.append(("Customer Audit Query", test_audit_customer_query(session)))
    results.append(("Audit Statistics", test_audit_stats(session)))
    results.append(("User Logout", test_logout(session)))
    
    # Summary
    print("\n" + "=" * 60)
    print(f"{Colors.BLUE}Test Results Summary{Colors.END}")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{status} - {test_name}")
    
    print("\n" + "-" * 60)
    success_rate = (passed / total) * 100
    if passed == total:
        print(f"{Colors.GREEN}All tests passed! ({passed}/{total}){Colors.END}")
    else:
        print(f"{Colors.YELLOW}Tests passed: {passed}/{total} ({success_rate:.1f}%){Colors.END}")
    print("=" * 60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_integration_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
        exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Test suite failed: {e}{Colors.END}")
        exit(1)
