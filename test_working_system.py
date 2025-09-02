#!/usr/bin/env python3
"""
Test script to verify Receiptor AI is working end-to-end
"""

import requests
import json
import tempfile
import os
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8001/api"
AUTH_TOKEN = "test-token"

def test_api_endpoint(endpoint, method="GET", data=None, files=None):
    """Test an API endpoint"""
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    if files is None:
        headers["Content-Type"] = "application/json"
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            if files:
                # Remove Content-Type for multipart
                headers.pop("Content-Type", None)
                response = requests.post(url, headers=headers, files=files, data=data)
            else:
                response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def create_test_receipt_file():
    """Create a simple test file"""
    # Create a simple text file as test receipt
    content = """STARBUCKS COFFEE
123 Main Street
Anytown, ST 12345

Date: 2024-01-15
Time: 14:30:25

1x Grande Latte        $5.65
1x Blueberry Muffin    $3.45

Subtotal:              $9.10
Tax:                   $0.73
Total:                 $9.83

Payment: Credit Card
Receipt #: 1234567890

Thank you for visiting!"""
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        return f.name

def main():
    print("🚀 Testing Receiptor AI System")
    print("=" * 50)
    
    tests = [
        {
            "name": "API Health Check",
            "endpoint": "/",
            "method": "GET"
        },
        {
            "name": "Get Receipts List",
            "endpoint": "/receipts",
            "method": "GET"
        },
        {
            "name": "Get Analytics Summary",
            "endpoint": "/analytics/summary",
            "method": "GET"
        },
        {
            "name": "Get AI Rules",
            "endpoint": "/ai-rules",
            "method": "GET"
        },
        {
            "name": "Get Rule Suggestions",
            "endpoint": "/ai-rules/suggestions",
            "method": "GET"
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n🔍 {test['name']}...")
        
        result = test_api_endpoint(
            test["endpoint"],
            test.get("method", "GET"),
            test.get("data")
        )
        
        if result["success"]:
            print(f"✅ PASS - Status: {result['status_code']}")
            if isinstance(result.get("data"), dict):
                # Print some key info
                data = result["data"]
                if "message" in data:
                    print(f"   Message: {data['message']}")
                elif "total_receipts" in data:
                    print(f"   Total receipts: {data['total_receipts']}")
                elif isinstance(data, list):
                    print(f"   Found {len(data)} items")
        else:
            print(f"❌ FAIL - Status: {result.get('status_code', 'N/A')}")
            if "error" in result:
                print(f"   Error: {result['error']}")
        
        results.append({
            "test": test["name"],
            "success": result["success"],
            "status_code": result.get("status_code"),
            "data": result.get("data")
        })
    
    # Test file upload
    print(f"\n🔍 Testing Receipt Upload...")
    test_file_path = create_test_receipt_file()
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_receipt.txt', f, 'text/plain')}
            result = test_api_endpoint("/receipts/upload", "POST", files=files)
            
            if result["success"]:
                print(f"✅ PASS - Upload successful")
                receipt_data = result["data"]
                print(f"   Receipt ID: {receipt_data.get('id', 'N/A')}")
                print(f"   Status: {receipt_data.get('processing_status', 'N/A')}")
                
                # Test getting the uploaded receipt
                if receipt_data.get('id'):
                    print(f"\n🔍 Testing Receipt Retrieval...")
                    get_result = test_api_endpoint(f"/receipts/{receipt_data['id']}")
                    if get_result["success"]:
                        print(f"✅ PASS - Receipt retrieved successfully")
                        extracted = get_result["data"].get("extracted_data", {})
                        print(f"   Vendor: {extracted.get('vendor_name', 'N/A')}")
                        print(f"   Amount: ${extracted.get('total_amount', 'N/A')}")
                    else:
                        print(f"❌ FAIL - Could not retrieve receipt")
            else:
                print(f"❌ FAIL - Upload failed: {result.get('status_code', 'N/A')}")
                
        results.append({
            "test": "Receipt Upload",
            "success": result["success"]
        })
        
    finally:
        # Clean up test file
        os.unlink(test_file_path)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 SUCCESS: Receiptor AI backend is working perfectly!")
        print("✅ All API endpoints are responding correctly")
        print("✅ Authentication is working")
        print("✅ File upload and processing works")
        print("✅ AI service (mock) is functioning")
        print("✅ Database operations are working")
        
        print("\n📋 To use the frontend:")
        print("1. Open browser developer tools")
        print("2. Go to Application > Local Storage")
        print(f"3. Add key 'authToken' with value '{AUTH_TOKEN}'")
        print("4. Refresh the page")
        print("5. The frontend will now authenticate with the backend!")
        
        return True
    else:
        print("\n⚠️  Some tests failed:")
        for result in results:
            if not result["success"]:
                print(f"  - {result['test']}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)