#!/usr/bin/env python3
"""
Test script for NTU Exchange University Recommendation API

Usage:
    python test_api.py
"""

import requests
import json
import time

# API configuration
API_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n" + "="*80)
    print("TEST 1: Health Check")
    print("="*80)

    response = requests.get(f"{API_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, "Health check failed"
    print("✓ Health check passed")


def test_search_endpoint():
    """Test the search endpoint with sample data"""
    print("\n" + "="*80)
    print("TEST 2: Search Universities")
    print("="*80)
    print("\nNOTE: This test requires valid NTU credentials.")
    print("First search takes 15-25 minutes, subsequent searches are instant.")
    print("\nPlease enter your NTU credentials:")

    # Get credentials from user
    username = input("  Username (e.g., AJITESH001): ").strip()
    if not username:
        print("✗ Skipping search test - no username provided")
        return

    password = input("  Password: ").strip()
    if not password:
        print("✗ Skipping search test - no password provided")
        return

    domain = input("  Domain (default: Student): ").strip() or "Student"

    # Prepare request payload
    payload = {
        "credentials": {
            "username": username,
            "password": password,
            "domain": domain
        },
        "target_countries": ["Australia", "Denmark"],  # Limit for faster testing
        "target_modules": ["SC4001", "SC4002"],        # Limit for faster testing
        "min_mappable_modules": 1,
        "use_cache": True
    }

    print(f"\nSending search request...")
    print(f"  Countries: {payload['target_countries']}")
    print(f"  Modules: {payload['target_modules']}")
    print(f"\nThis may take 15-25 minutes on first run...")

    start_time = time.time()
    response = requests.post(f"{API_URL}/api/search", json=payload)
    elapsed = time.time() - start_time

    print(f"\nCompleted in {elapsed:.1f} seconds")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Search successful!")
        print(f"  Results found: {data['results_count']}")
        print(f"  Cache used: {data['cache_used']}")
        print(f"  Execution time: {data['execution_time_seconds']}s")

        if data['results_count'] > 0:
            print(f"\n  Top 3 universities:")
            for uni in data['results'][:3]:
                print(f"    {uni['rank']}. {uni['name']} ({uni['country']}) - {uni['mappable_count']} modules")
    else:
        print(f"✗ Search failed")
        print(f"Error: {response.json()}")


def test_cache_endpoints():
    """Test cache management endpoints"""
    print("\n" + "="*80)
    print("TEST 3: Cache Management")
    print("="*80)

    # Test cache clear
    print("\nClearing all caches...")
    response = requests.post(f"{API_URL}/api/cache/clear")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Cache cleared")
        print(f"  Items cleared: {len(data['cleared_items'])}")
        for item in data['cleared_items']:
            print(f"    - {item}")
    else:
        print(f"Response: {response.json()}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("NTU EXCHANGE UNIVERSITY API - TEST SUITE")
    print("="*80)
    print(f"\nTesting API at: {API_URL}")
    print("Make sure the API server is running (python run_api.py)")

    try:
        # Test 1: Health check
        test_health_endpoint()

        # Test 2: Search (requires user input for credentials)
        proceed = input("\n\nRun search test? This requires NTU credentials (y/n): ").strip().lower()
        if proceed == 'y':
            test_search_endpoint()
        else:
            print("✓ Skipping search test")

        # Test 3: Cache management
        test_cache_endpoints()

        print("\n" + "="*80)
        print("✓ ALL TESTS COMPLETED")
        print("="*80 + "\n")

    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to API server")
        print("   Please start the server first: python run_api.py\n")
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
