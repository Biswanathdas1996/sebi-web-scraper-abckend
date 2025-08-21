#!/usr/bin/env python3
"""
Test script for the SEBI Circular API endpoint
"""

import requests
import json
import urllib.parse

def test_sebi_circular_api():
    """Test the SEBI circular API endpoint"""
    
    base_url = "http://localhost:8000"
    
    # Test cases with different circular references from the metadata
    test_cases = [
        "SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/118",
        "SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/116", 
        "SEBI/HO/IMD/PoD1/CIR/P/2025/115",
        "SEBI/HO/DDHS/DDHS-PoD-2/P/CIR/2025/114"
    ]
    
    print("🧪 Testing SEBI Circular API Endpoint")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Test 2: Valid circular references
    print("\n2. Testing valid circular references...")
    for i, circular_ref in enumerate(test_cases, 1):
        try:
            # URL encode the circular reference
            encoded_ref = urllib.parse.quote(circular_ref, safe='')
            url = f"{base_url}/api/sebi-circular/{encoded_ref}"
            
            print(f"   {i}. Testing: {circular_ref}")
            print(f"      URL: {url}")
            
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Success - Found content for '{data.get('sebi_circular_ref', 'Unknown')}'")
                print(f"      📄 Title: {data.get('document_title', 'No title')[:100]}...")
                print(f"      📅 Date: {data.get('circular_date', 'No date')}")
                
                # Check if extracted content exists
                if data.get('extracted_content'):
                    content = data['extracted_content']
                    text_length = len(content.get('text', ''))
                    print(f"      📊 Content length: {text_length} characters")
                else:
                    print(f"      ⚠️  No extracted content found")
                    
            elif response.status_code == 404:
                print(f"      ❌ Not found: {circular_ref}")
                if response.headers.get('content-type', '').startswith('application/json'):
                    error_data = response.json()
                    if 'available_references' in error_data:
                        print(f"      📋 Available references: {len(error_data['available_references'])} found")
            else:
                print(f"      ❌ Error {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"      ❌ Exception: {e}")
    
    # Test 3: Invalid circular reference
    print("\n3. Testing invalid circular reference...")
    try:
        invalid_ref = "INVALID/REF/123"
        encoded_ref = urllib.parse.quote(invalid_ref, safe='')
        url = f"{base_url}/api/sebi-circular/{encoded_ref}"
        
        response = requests.get(url)
        
        if response.status_code == 404:
            data = response.json()
            print(f"   ✅ Correctly returned 404 for invalid reference")
            if 'available_references' in data:
                print(f"   📋 API returned {len(data['available_references'])} available references")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 4: Check API documentation
    print("\n4. Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/api/docs")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ API documentation accessible")
            if 'file_endpoints' in data and 'GET /api/sebi-circular/<sebi_circular_ref>' in str(data['file_endpoints']):
                print("   ✅ New endpoint documented correctly")
            else:
                print("   ⚠️  New endpoint not found in documentation")
        else:
            print(f"   ❌ Documentation error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Documentation exception: {e}")

    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_sebi_circular_api()
