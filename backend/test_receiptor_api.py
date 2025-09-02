#!/usr/bin/env python3
"""
Test script for Receiptor AI API endpoints
Tests all major functionality including upload, processing, rules, integrations, and compliance.
"""

import asyncio
import aiohttp
import json
import os
import tempfile
from datetime import datetime, timedelta
# from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
API_BASE_URL = "http://localhost:8001/api"
TEST_USER_TOKEN = "test-user-token"  # Mock token for testing

class ReceiptorAPITester:
    def __init__(self):
        self.session = None
        self.headers = {
            "Authorization": f"Bearer {TEST_USER_TOKEN}",
            "Content-Type": "application/json"
        }
        self.test_results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def create_test_receipt_image(self) -> bytes:
        """Create a test receipt image (simplified for testing)"""
        # Create a simple test image without PIL
        # This is a minimal 1x1 PNG for testing
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

    async def test_health_check(self):
        """Test basic API health"""
        try:
            async with self.session.get(f"{API_BASE_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("API Health Check", True, f"Response: {data.get('message', 'OK')}")
                else:
                    self.log_result("API Health Check", False, f"Status: {response.status}")
        except Exception as e:
            self.log_result("API Health Check", False, f"Error: {str(e)}")

    async def test_receipt_upload(self):
        """Test receipt upload functionality"""
        try:
            # Create test image
            img_data = self.create_test_receipt_image()
            
            # Prepare multipart form data
            data = aiohttp.FormData()
            data.add_field('file', img_data, filename='test_receipt.png', content_type='image/png')
            
            # Upload headers (remove Content-Type for multipart)
            upload_headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
            
            async with self.session.post(
                f"{API_BASE_URL}/receipts/upload",
                data=data,
                headers=upload_headers
            ) as response:
                if response.status == 200:
                    receipt_data = await response.json()
                    self.uploaded_receipt_id = receipt_data.get('id')
                    
                    self.log_result(
                        "Receipt Upload", 
                        True, 
                        f"Receipt ID: {self.uploaded_receipt_id}, Status: {receipt_data.get('processing_status')}"
                    )
                    return receipt_data
                else:
                    error_text = await response.text()
                    self.log_result("Receipt Upload", False, f"Status: {response.status}, Error: {error_text}")
                    return None
                    
        except Exception as e:
            self.log_result("Receipt Upload", False, f"Error: {str(e)}")
            return None

    async def test_receipt_retrieval(self, receipt_id: str):
        """Test receipt retrieval"""
        try:
            async with self.session.get(
                f"{API_BASE_URL}/receipts/{receipt_id}",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    receipt_data = await response.json()
                    extracted_data = receipt_data.get('extracted_data', {})
                    
                    self.log_result(
                        "Receipt Retrieval", 
                        True, 
                        f"Vendor: {extracted_data.get('vendor_name')}, Amount: ${extracted_data.get('total_amount')}"
                    )
                    return receipt_data
                else:
                    self.log_result("Receipt Retrieval", False, f"Status: {response.status}")
                    return None
                    
        except Exception as e:
            self.log_result("Receipt Retrieval", False, f"Error: {str(e)}")
            return None

    async def test_receipt_list(self):
        """Test receipt listing"""
        try:
            async with self.session.get(
                f"{API_BASE_URL}/receipts",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    receipts = await response.json()
                    self.log_result(
                        "Receipt List", 
                        True, 
                        f"Found {len(receipts)} receipts"
                    )
                    return receipts
                else:
                    self.log_result("Receipt List", False, f"Status: {response.status}")
                    return None
                    
        except Exception as e:
            self.log_result("Receipt List", False, f"Error: {str(e)}")
            return None

    async def test_ai_rule_creation(self):
        """Test AI rule creation"""
        try:
            rule_data = {
                "user_id": "user123",
                "name": "Auto-categorize Starbucks",
                "description": "Automatically categorize Starbucks receipts as meals & entertainment",
                "conditions": {
                    "logic": "AND",
                    "conditions": [
                        {
                            "type": "text",
                            "field": "extracted_data.vendor_name",
                            "operator": "contains",
                            "value": "starbucks"
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
            
            async with self.session.post(
                f"{API_BASE_URL}/ai-rules",
                headers=self.headers,
                json=rule_data
            ) as response:
                if response.status == 200:
                    rule = await response.json()
                    self.created_rule_id = rule.get('id')
                    
                    self.log_result(
                        "AI Rule Creation", 
                        True, 
                        f"Rule ID: {self.created_rule_id}, Name: {rule.get('name')}"
                    )
                    return rule
                else:
                    error_text = await response.text()
                    self.log_result("AI Rule Creation", False, f"Status: {response.status}, Error: {error_text}")
                    return None
                    
        except Exception as e:
            self.log_result("AI Rule Creation", False, f"Error: {str(e)}")
            return None

    async def test_ai_rule_testing(self, rule_id: str):
        """Test AI rule testing functionality"""
        try:
            async with self.session.post(
                f"{API_BASE_URL}/ai-rules/{rule_id}/test",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    test_results = await response.json()
                    
                    self.log_result(
                        "AI Rule Testing", 
                        True, 
                        f"Tested: {test_results.get('total_tested')}, Matched: {test_results.get('total_matched')}"
                    )
                    return test_results
                else:
                    self.log_result("AI Rule Testing", False, f"Status: {response.status}")
                    return None
                    
        except Exception as e:
            self.log_result("AI Rule Testing", False, f"Error: {str(e)}")
            return None

    async def test_analytics(self):
        """Test analytics endpoint"""
        try:
            async with self.session.get(
                f"{API_BASE_URL}/analytics/summary",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    analytics = await response.json()
                    
                    self.log_result(
                        "Analytics Summary", 
                        True, 
                        f"Total receipts: {analytics.get('total_receipts')}, Categories: {len(analytics.get('category_breakdown', []))}"
                    )
                    return analytics
                else:
                    self.log_result("Analytics Summary", False, f"Status: {response.status}")
                    return None
                    
        except Exception as e:
            self.log_result("Analytics Summary", False, f"Error: {str(e)}")
            return None

    async def test_compliance_validation(self, receipt_id: str):
        """Test compliance validation"""
        try:
            async with self.session.get(
                f"{API_BASE_URL}/compliance/validate/{receipt_id}",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    validation = await response.json()
                    
                    self.log_result(
                        "Compliance Validation", 
                        True, 
                        f"Overall compliant: {validation.get('overall_compliant')}"
                    )
                    return validation
                else:
                    self.log_result("Compliance Validation", False, f"Status: {response.status}")
                    return None
                    
        except Exception as e:
            self.log_result("Compliance Validation", False, f"Error: {str(e)}")
            return None

    async def test_audit_trail(self):
        """Test audit trail functionality"""
        try:
            async with self.session.get(
                f"{API_BASE_URL}/audit/trail",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    audit_data = await response.json()
                    
                    self.log_result(
                        "Audit Trail", 
                        True, 
                        f"Found {audit_data.get('count')} audit events"
                    )
                    return audit_data
                else:
                    self.log_result("Audit Trail", False, f"Status: {response.status}")
                    return None
                    
        except Exception as e:
            self.log_result("Audit Trail", False, f"Error: {str(e)}")
            return None

    async def test_rule_suggestions(self):
        """Test AI rule suggestions"""
        try:
            async with self.session.get(
                f"{API_BASE_URL}/ai-rules/suggestions",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    suggestions = await response.json()
                    
                    self.log_result(
                        "Rule Suggestions", 
                        True, 
                        f"Found {suggestions.get('count')} rule suggestions"
                    )
                    return suggestions
                else:
                    self.log_result("Rule Suggestions", False, f"Status: {response.status}")
                    return None
                    
        except Exception as e:
            self.log_result("Rule Suggestions", False, f"Error: {str(e)}")
            return None

    async def test_compliance_export(self):
        """Test compliance export functionality"""
        try:
            start_date = (datetime.now() - timedelta(days=30)).date().isoformat()
            end_date = datetime.now().date().isoformat()
            
            async with self.session.get(
                f"{API_BASE_URL}/compliance/export/receipts",
                headers=self.headers,
                params={
                    "start_date": start_date,
                    "end_date": end_date,
                    "format": "csv"
                }
            ) as response:
                if response.status == 200:
                    export_data = await response.json()
                    
                    self.log_result(
                        "Compliance Export", 
                        True, 
                        f"Exported {export_data.get('record_count')} records"
                    )
                    return export_data
                else:
                    self.log_result("Compliance Export", False, f"Status: {response.status}")
                    return None
                    
        except Exception as e:
            self.log_result("Compliance Export", False, f"Error: {str(e)}")
            return None

    async def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Receiptor AI API Tests")
        print("=" * 50)
        
        # Initialize variables
        self.uploaded_receipt_id = None
        self.created_rule_id = None
        
        # Basic tests
        await self.test_health_check()
        
        # Receipt management tests
        receipt_data = await self.test_receipt_upload()
        if receipt_data and self.uploaded_receipt_id:
            await self.test_receipt_retrieval(self.uploaded_receipt_id)
            await self.test_compliance_validation(self.uploaded_receipt_id)
        
        await self.test_receipt_list()
        
        # AI rules tests
        rule_data = await self.test_ai_rule_creation()
        if rule_data and self.created_rule_id:
            await self.test_ai_rule_testing(self.created_rule_id)
        
        await self.test_rule_suggestions()
        
        # Analytics and compliance tests
        await self.test_analytics()
        await self.test_audit_trail()
        await self.test_compliance_export()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        # Save detailed results
        with open('test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\nDetailed results saved to: test_results.json")
        
        return passed_tests == total_tests

async def main():
    """Main test function"""
    try:
        async with ReceiptorAPITester() as tester:
            success = await tester.run_all_tests()
            
            if success:
                print("\n🎉 All tests passed! Receiptor AI is working correctly.")
                return 0
            else:
                print("\n⚠️  Some tests failed. Check the results above.")
                return 1
                
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())