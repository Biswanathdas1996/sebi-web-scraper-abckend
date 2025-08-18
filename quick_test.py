"""
Quick test script for Database API
"""

import json
import urllib.request
import urllib.error

def test_endpoint(url, description):
    """Test a single endpoint"""
    print(f"Testing: {description}")
    print(f"URL: {url}")
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print(f"✅ Success: {response.status}")
                
                # Print summary based on endpoint
                if 'tables' in data and 'total_records' in data:
                    print(f"   Total records: {data['total_records']}")
                    print(f"   Total tables: {data['total_tables']}")
                elif 'table_counts' in data:
                    print(f"   Database health: {data.get('database_health', 'unknown')}")
                    table_counts = data['table_counts']
                    total = sum(table_counts.values())
                    print(f"   Total records: {total}")
                elif 'data' in data and isinstance(data['data'], list):
                    print(f"   Records returned: {len(data['data'])}")
                    print(f"   Total in table: {data.get('total_records', 'unknown')}")
                elif 'message' in data:
                    print(f"   Message: {data['message']}")
                
                print()
                return True
            else:
                print(f"❌ Failed: {response.status}")
                print()
                return False
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        print()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        return False

def main():
    """Run quick tests"""
    print("🚀 Quick Database API Test")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    tests = [
        (f"{base_url}/", "Health Check"),
        (f"{base_url}/api/database/summary", "Database Summary"),
        (f"{base_url}/api/database/schema", "Database Schema"),
        (f"{base_url}/api/database/table/teams?limit=5", "Teams Table"),
        (f"{base_url}/api/database/table/sebi_documents?limit=5", "SEBI Documents Table"),
    ]
    
    passed = 0
    for url, description in tests:
        if test_endpoint(url, description):
            passed += 1
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! The API is working correctly.")
        
        # Test the full data fetch (optional)
        print("\nTesting full data fetch (may take a moment)...")
        if test_endpoint(f"{base_url}/api/database/tables", "All Tables Data"):
            print("✅ Full data fetch also works!")
        else:
            print("⚠️ Full data fetch failed, but core API is working")
    else:
        print("⚠️ Some tests failed. Check the server and database connection.")

if __name__ == "__main__":
    main()
