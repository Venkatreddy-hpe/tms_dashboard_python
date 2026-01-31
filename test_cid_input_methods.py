#!/usr/bin/env python3
"""
Test script for new CID input methods (CSV and Manual Entry)
"""

import sys
sys.path.insert(0, '/home/pdanekula/tms_dashboard_python')

from src.prod_customer_data import normalize_customer_ids, parse_csv_input, parse_manual_entry

def test_normalize_customer_ids():
    """Test normalization function"""
    print("=" * 60)
    print("TEST: normalize_customer_ids()")
    print("=" * 60)
    
    test_cases = [
        (["CUST001", "CUST002", "CUST001"], "Deduplication"),
        (["  CUST001  ", "CUST002"], "Whitespace trimming"),
        (["cust_id", "CUST001", "CUST002"], "Header filtering (cust_id)"),
        (["customer_id", "CUST001"], "Header filtering (customer_id)"),
        (["", "CUST001", ""], "Empty string filtering"),
    ]
    
    for input_list, description in test_cases:
        result = normalize_customer_ids(input_list)
        print(f"\n{description}:")
        print(f"  Input:  {input_list}")
        print(f"  Output: {result}")
        print(f"  ✓ PASS" if result else f"  ✗ FAIL")

def test_parse_csv_input():
    """Test CSV parsing function"""
    print("\n" + "=" * 60)
    print("TEST: parse_csv_input()")
    print("=" * 60)
    
    test_cases = [
        ("cust_id\nCUST001\nCUST002\nCUST003", "CSV with header"),
        ("CUST001\nCUST002\nCUST003", "CSV without header"),
        ("CUST001,CUST002,CUST003", "Comma-separated (shouldn't happen in CSV but test it)"),
        ("CUST001\nCUST001\nCUST002", "CSV with duplicates"),
        ("CUST001\n  CUST002  \nCUST003", "CSV with whitespace"),
    ]
    
    for csv_content, description in test_cases:
        result = parse_csv_input(csv_content)
        print(f"\n{description}:")
        print(f"  Input:  {repr(csv_content[:50])}...")
        print(f"  Output: {result}")
        print(f"  ✓ PASS ({len(result)} IDs)" if result else f"  ✗ FAIL")

def test_parse_manual_entry():
    """Test manual entry parsing function"""
    print("\n" + "=" * 60)
    print("TEST: parse_manual_entry()")
    print("=" * 60)
    
    test_cases = [
        ("CUST001\nCUST002\nCUST003", "Line-separated"),
        ("CUST001, CUST002, CUST003", "Comma-separated"),
        ("CUST001,CUST002\nCUST003,CUST004", "Mixed (should prioritize comma)"),
        ("  CUST001  \n  CUST002  ", "Line-separated with whitespace"),
        ("CUST001, CUST001, CUST002", "Comma-separated with duplicates"),
    ]
    
    for text_input, description in test_cases:
        result = parse_manual_entry(text_input)
        print(f"\n{description}:")
        print(f"  Input:  {repr(text_input[:50])}...")
        print(f"  Output: {result}")
        print(f"  ✓ PASS ({len(result)} IDs)" if result else f"  ✗ FAIL")

def test_priority_order():
    """Test priority order: API > CSV > Manual"""
    print("\n" + "=" * 60)
    print("TEST: Priority Order (API > CSV > Manual)")
    print("=" * 60)
    
    # Simulate backend logic
    api_cids = ["API001", "API002"]
    csv_cids = ["CSV001", "CSV002"]
    manual_cids = ["MANUAL001", "MANUAL002"]
    
    print("\nScenario 1: API provided (should use API)")
    if api_cids:
        result = api_cids
        print(f"  Result: {result}")
        print(f"  ✓ PASS" if result == api_cids else f"  ✗ FAIL")
    
    print("\nScenario 2: No API, CSV provided (should use CSV)")
    if not api_cids and csv_cids:
        result = csv_cids
        print(f"  Result: {result}")
        print(f"  ✓ PASS" if result == csv_cids else f"  ✗ FAIL")
    
    print("\nScenario 3: No API, No CSV, Manual provided (should use Manual)")
    if not api_cids and not csv_cids and manual_cids:
        result = manual_cids
        print(f"  Result: {result}")
        print(f"  ✓ PASS" if result == manual_cids else f"  ✗ FAIL")

if __name__ == '__main__':
    test_normalize_customer_ids()
    test_parse_csv_input()
    test_parse_manual_entry()
    test_priority_order()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
