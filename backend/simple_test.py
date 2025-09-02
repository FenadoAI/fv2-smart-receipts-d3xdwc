#!/usr/bin/env python3
"""
Simple test script to verify Receiptor AI backend imports and basic functionality
"""

import sys
import os
import json
from datetime import datetime

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test basic FastAPI imports
        from fastapi import FastAPI, APIRouter
        from starlette.middleware.cors import CORSMiddleware
        print("✅ FastAPI imports successful")
        
        # Test our models
        from server import (
            Receipt, ReceiptCreate, ReceiptUpdate,
            AIRule, AIRuleCreate,
            IntegrationConfig, IntegrationConfigCreate,
            ExtractedData, User, UserCreate
        )
        print("✅ Model imports successful")
        
        # Test AI service (mock)
        from ai_service_mock import ai_processor
        print("✅ AI service import successful (mock)")
        
        # Test integrations (mock)
        from integrations_mock import integration_manager
        print("✅ Integration manager import successful (mock)")
        
        # Test rules engine
        from ai_rules_engine import get_rules_engine, ConditionEvaluator, ActionExecutor
        print("✅ AI rules engine import successful")
        
        # Test compliance
        from compliance import (
            get_audit_logger, get_retention_manager, get_compliance_reporter,
            compliance_validator, AuditEventType
        )
        print("✅ Compliance module import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_data_models():
    """Test that data models work correctly"""
    print("\n🔍 Testing data models...")
    
    try:
        from server import Receipt, ExtractedData, AIRule
        
        # Test ExtractedData
        extracted_data = ExtractedData(
            vendor_name="Test Store",
            total_amount=25.99,
            tax_amount=2.08,
            date=datetime.now(),
            description="Test purchase"
        )
        print("✅ ExtractedData model works")
        
        # Test Receipt
        receipt = Receipt(
            user_id="test_user",
            filename="test_receipt.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            extracted_data=extracted_data
        )
        print("✅ Receipt model works")
        
        # Test serialization
        receipt_dict = receipt.dict()
        assert receipt_dict['user_id'] == "test_user"
        assert receipt_dict['extracted_data']['vendor_name'] == "Test Store"
        print("✅ Model serialization works")
        
        return True
        
    except Exception as e:
        print(f"❌ Data model test failed: {e}")
        return False

def test_ai_processor():
    """Test the AI processor (mock)"""
    print("\n🔍 Testing AI processor...")
    
    try:
        import asyncio
        from ai_service_mock import ai_processor
        
        async def test_processing():
            result = await ai_processor.process_receipt("/tmp/test.jpg", "image/jpeg")
            
            assert 'extracted_data' in result
            assert 'category' in result
            assert 'confidence_score' in result
            assert isinstance(result['confidence_score'], float)
            assert 0 <= result['confidence_score'] <= 1
            
            print(f"✅ AI processing returned: vendor={result['extracted_data']['vendor_name']}, amount=${result['extracted_data']['total_amount']}")
            return True
        
        # Run async test
        success = asyncio.run(test_processing())
        return success
        
    except Exception as e:
        print(f"❌ AI processor test failed: {e}")
        return False

def test_rules_engine():
    """Test the rules engine"""
    print("\n🔍 Testing rules engine...")
    
    try:
        from ai_rules_engine import ConditionEvaluator
        
        # Test condition evaluation
        evaluator = ConditionEvaluator()
        
        # Test data
        receipt_data = {
            'extracted_data': {
                'vendor_name': 'Starbucks Coffee',
                'total_amount': 9.83,
                'date': datetime.now()
            },
            'category': 'meals_entertainment'
        }
        
        # Test text condition
        condition = {
            'type': 'text',
            'field': 'extracted_data.vendor_name',
            'operator': 'contains',
            'value': 'starbucks'
        }
        
        result = evaluator.evaluate_condition(condition, receipt_data)
        assert result == True
        print("✅ Text condition evaluation works")
        
        # Test number condition
        condition = {
            'type': 'number',
            'field': 'extracted_data.total_amount',
            'operator': 'greater_than',
            'value': 5.0
        }
        
        result = evaluator.evaluate_condition(condition, receipt_data)
        assert result == True
        print("✅ Number condition evaluation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Rules engine test failed: {e}")
        return False

def test_compliance():
    """Test compliance features"""
    print("\n🔍 Testing compliance...")
    
    try:
        from compliance import compliance_validator
        
        # Test receipt data
        receipt_data = {
            'extracted_data': {
                'vendor_name': 'Test Store',
                'total_amount': 25.99,
                'tax_amount': 2.08,
                'date': datetime.now(),
                'description': 'Test purchase',
                'receipt_number': '12345'
            },
            'category': 'office_supplies'
        }
        
        # Test completeness validation
        validation = compliance_validator.validate_receipt_completeness(receipt_data)
        assert 'is_compliant' in validation
        assert 'score' in validation
        assert 0 <= validation['score'] <= 1
        print(f"✅ Compliance validation works: score={validation['score']:.2f}")
        
        # Test tax validation
        tax_validation = compliance_validator.validate_tax_requirements(receipt_data)
        assert 'is_compliant' in tax_validation
        print("✅ Tax compliance validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Compliance test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Receiptor AI Backend Tests")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Data Models", test_data_models),
        ("AI Processor", test_ai_processor),
        ("Rules Engine", test_rules_engine),
        ("Compliance", test_compliance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
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
        print("\n🎉 All backend tests passed! Core functionality is working.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())