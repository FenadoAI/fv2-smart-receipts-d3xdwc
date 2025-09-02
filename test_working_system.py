#!/usr/bin/env python3
"""
Test the working Receiptor AI system
"""

import requests
import json
import time
import io
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8002/api"
TEST_TOKEN = "test-token"

def test_api_health():
    """Test if API is responding"""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health: {data.get('message')}")
            return True
        else:
            print(f"❌ API Health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health error: {e}")
        return False

def create_test_image():
    """Create a simple test image file"""
    # Create a minimal valid PNG
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    return png_data

def test_receipt_upload():
    """Test receipt upload functionality"""
    try:
        # Create test image
        image_data = create_test_image()
        
        # Prepare the file upload
        files = {
            'file': ('test_receipt.png', image_data, 'image/png')
        }
        
        headers = {
            'Authorization': f'Bearer {TEST_TOKEN}'
        }
        
        response = requests.post(
            f"{API_BASE_URL}/receipts/upload",
            files=files,
            headers=headers
        )
        
        if response.status_code == 200:
            receipt = response.json()
            print(f"✅ Receipt Upload: ID={receipt.get('id')[:8]}..., Status={receipt.get('processing_status')}")
            
            # Check if AI processing worked
            if receipt.get('extracted_data'):
                vendor = receipt['extracted_data'].get('vendor_name')
                amount = receipt['extracted_data'].get('total_amount')
                print(f"   📄 AI Extracted: {vendor}, ${amount}")
            
            return receipt
        else:
            print(f"❌ Receipt Upload failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Receipt Upload error: {e}")
        return None

def test_receipt_list():
    """Test receipt listing"""
    try:
        headers = {
            'Authorization': f'Bearer {TEST_TOKEN}'
        }
        
        response = requests.get(
            f"{API_BASE_URL}/receipts",
            headers=headers
        )
        
        if response.status_code == 200:
            receipts = response.json()
            print(f"✅ Receipt List: Found {len(receipts)} receipts")
            return receipts
        else:
            print(f"❌ Receipt List failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Receipt List error: {e}")
        return None

def test_ai_rule_creation():
    """Test AI rule creation"""
    try:
        headers = {
            'Authorization': f'Bearer {TEST_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        rule_data = {
            "user_id": "user123",
            "name": "Test Rule - Coffee Shops",
            "description": "Auto-categorize coffee shop receipts",
            "conditions": {
                "logic": "AND",
                "conditions": [
                    {
                        "type": "text",
                        "field": "extracted_data.vendor_name",
                        "operator": "contains",
                        "value": "coffee"
                    }
                ]
            },
            "actions": {
                "set_category": {
                    "category": "meals_entertainment"
                },
                "add_tags": {
                    "tags": ["coffee", "auto-categorized"]
                }
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/ai-rules",
            headers=headers,
            json=rule_data
        )
        
        if response.status_code == 200:
            rule = response.json()
            print(f"✅ AI Rule Created: {rule.get('name')}")
            return rule
        else:
            print(f"❌ AI Rule creation failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ AI Rule creation error: {e}")
        return None

def test_analytics():
    """Test analytics endpoint"""
    try:
        headers = {
            'Authorization': f'Bearer {TEST_TOKEN}'
        }
        
        response = requests.get(
            f"{API_BASE_URL}/analytics/summary",
            headers=headers
        )
        
        if response.status_code == 200:
            analytics = response.json()
            total_receipts = analytics.get('total_receipts', 0)
            total_amount = analytics.get('total_amount', 0)
            categories = len(analytics.get('category_breakdown', []))
            
            print(f"✅ Analytics: {total_receipts} receipts, ${total_amount:.2f} total, {categories} categories")
            return analytics
        else:
            print(f"❌ Analytics failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        return None

def test_audit_trail():
    """Test audit trail"""
    try:
        headers = {
            'Authorization': f'Bearer {TEST_TOKEN}'
        }
        
        response = requests.get(
            f"{API_BASE_URL}/audit/trail",
            headers=headers
        )
        
        if response.status_code == 200:
            audit_data = response.json()
            event_count = audit_data.get('count', 0)
            print(f"✅ Audit Trail: {event_count} events logged")
            return audit_data
        else:
            print(f"❌ Audit Trail failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Audit Trail error: {e}")
        return None

def main():
    """Run all tests"""
    print("🚀 Testing Receiptor AI System")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    tests = [
        ("API Health Check", test_api_health),
        ("Receipt Upload & AI Processing", test_receipt_upload),
        ("Receipt List", test_receipt_list),
        ("AI Rule Creation", test_ai_rule_creation),
        ("Analytics Summary", test_analytics),
        ("Audit Trail", test_audit_trail)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        try:
            result = test_func()
            success = result is not None
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 System Test Summary")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Receiptor AI is working correctly!")
        print("\n💡 System is ready for use:")
        print("   • Backend API: http://localhost:8002")
        print("   • Upload receipts via POST /api/receipts/upload")
        print("   • View receipts via GET /api/receipts")
        print("   • Create AI rules via POST /api/ai-rules")
        print("   • Get analytics via GET /api/analytics/summary")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    exit(main())