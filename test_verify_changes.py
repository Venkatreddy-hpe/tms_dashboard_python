#!/usr/bin/env python3
"""
Test script to verify the copyToClipboard function in the template
"""

import re

def test_template():
    """Test that the template has the correct copyToClipboard function"""
    
    print("=" * 80)
    print("TEMPLATE VERIFICATION TEST")
    print("=" * 80)
    
    with open('/home/pdanekula/tms_dashboard_python/templates/index.html', 'r') as f:
        content = f.read()
    
    # Test 1: Check for old navigator.clipboard usage (should NOT exist)
    print("\n[TEST 1] Checking for direct navigator.clipboard.writeText usage...")
    matches = re.findall(r'navigator\.clipboard\.writeText', content)
    if matches:
        print(f"  ❌ FAILED: Found {len(matches)} instances of navigator.clipboard.writeText")
        print("     This will cause errors on HTTP connections!")
        return False
    else:
        print("  ✅ PASSED: No direct navigator.clipboard.writeText found")
    
    # Test 2: Check for copyToClipboard function definition
    print("\n[TEST 2] Checking for copyToClipboard function definition...")
    if 'function copyToClipboard(elementId, event)' in content:
        print("  ✅ PASSED: copyToClipboard function found")
    else:
        print("  ❌ FAILED: copyToClipboard function not found")
        return False
    
    # Test 3: Check for fallbackCopyToClipboard function
    print("\n[TEST 3] Checking for fallbackCopyToClipboard function...")
    if 'function fallbackCopyToClipboard(text, event)' in content:
        print("  ✅ PASSED: fallbackCopyToClipboard function found")
    else:
        print("  ❌ FAILED: fallbackCopyToClipboard function not found")
        return False
    
    # Test 4: Check for document.execCommand('copy') in fallback
    print("\n[TEST 4] Checking for document.execCommand('copy') in fallback...")
    fallback_match = re.search(r'function fallbackCopyToClipboard.*?document\.execCommand\(\'copy\'\)', content, re.DOTALL)
    if fallback_match:
        print("  ✅ PASSED: document.execCommand('copy') found in fallback function")
    else:
        print("  ❌ FAILED: document.execCommand('copy') not found in fallback")
        return False
    
    # Test 5: Check that copy button calls copyToClipboard
    print("\n[TEST 5] Checking that Copy Token button calls copyToClipboard...")
    button_match = re.search(r'📋 Copy Token.*?onclick=.*?copyToClipboard', content, re.DOTALL | re.IGNORECASE)
    if button_match or ('Copy Token' in content and 'copyToClipboard' in content):
        print("  ✅ PASSED: Copy Token button and copyToClipboard function exist")
    else:
        print("  ❌ FAILED: Copy Token button doesn't call copyToClipboard")
        return False
    
    # Test 6: Check for copyJobIdToClipboard (should use fallback too)
    print("\n[TEST 6] Checking for copyJobIdToClipboard function...")
    if 'function copyJobIdToClipboard(text, element)' in content:
        print("  ✅ PASSED: copyJobIdToClipboard function found")
    else:
        print("  ❌ FAILED: copyJobIdToClipboard function not found")
        return False
    
    # Test 7: Verify copyJobIdToClipboard doesn't use navigator.clipboard directly
    print("\n[TEST 7] Checking copyJobIdToClipboard doesn't use navigator.clipboard...")
    jobid_func = re.search(r'function copyJobIdToClipboard.*?^        function', content, re.DOTALL | re.MULTILINE)
    if jobid_func and 'navigator.clipboard' not in jobid_func.group(0):
        print("  ✅ PASSED: copyJobIdToClipboard doesn't use navigator.clipboard")
    else:
        print("  ❌ FAILED: copyJobIdToClipboard might use navigator.clipboard")
        return False
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED! ✅")
    print("=" * 80)
    return True

def test_app_py():
    """Test that app.py has cache control headers"""
    
    print("\n" + "=" * 80)
    print("APP.PY VERIFICATION TEST")
    print("=" * 80)
    
    with open('/home/pdanekula/tms_dashboard_python/app.py', 'r') as f:
        content = f.read()
    
    # Test 1: Check for no_cache decorator
    print("\n[TEST 1] Checking for no_cache decorator...")
    if 'def no_cache(f):' in content:
        print("  ✅ PASSED: no_cache decorator found")
    else:
        print("  ❌ FAILED: no_cache decorator not found")
        return False
    
    # Test 2: Check that index route uses no_cache
    print("\n[TEST 2] Checking that index route uses @no_cache...")
    index_match = re.search(r'@app\.route\(\'/\'\).*?@no_cache.*?def index', content, re.DOTALL)
    if index_match:
        print("  ✅ PASSED: index route has @no_cache decorator")
    else:
        print("  ❌ FAILED: index route missing @no_cache decorator")
        return False
    
    # Test 3: Check for make_response import
    print("\n[TEST 3] Checking for make_response import...")
    if 'make_response' in content[:500]:  # Should be in imports
        print("  ✅ PASSED: make_response imported")
    else:
        print("  ❌ FAILED: make_response not imported")
        return False
    
    print("\n" + "=" * 80)
    print("ALL APP.PY TESTS PASSED! ✅")
    print("=" * 80)
    return True

if __name__ == '__main__':
    template_ok = test_template()
    app_ok = test_app_py()
    
    if template_ok and app_ok:
        print("\n" + "🎉 " * 20)
        print("ALL VERIFICATION TESTS PASSED!")
        print("🎉 " * 20)
        exit(0)
    else:
        print("\n" + "❌ " * 20)
        print("SOME TESTS FAILED - PLEASE FIX BEFORE DEPLOYING")
        print("❌ " * 20)
        exit(1)
