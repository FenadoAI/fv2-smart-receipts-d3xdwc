#!/usr/bin/env python3
"""
Test receipt upload without authentication
"""

import requests
import tempfile
import os

def create_minimal_png():
    """Create a minimal PNG file for testing"""
    # This is a minimal 1x1 PNG in bytes
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(png_data)
        return f.name

def test_upload():
    """Test uploading a receipt"""
    print("🔍 Testing receipt upload without authentication...")
    
    # Create test image
    image_path = create_minimal_png()
    
    try:
        # Upload without auth headers
        with open(image_path, 'rb') as f:
            files = {'file': ('test_receipt.png', f, 'image/png')}
            response = requests.post('http://localhost:8001/api/receipts/upload', files=files)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Upload worked without authentication")
            print(f"Receipt ID: {data.get('id')}")
            print(f"Processing Status: {data.get('processing_status')}")
            print(f"Filename: {data.get('filename')}")
            
            # Wait a bit for processing
            import time
            time.sleep(2)
            
            # Check if we can retrieve it
            receipt_id = data.get('id')
            if receipt_id:
                get_response = requests.get(f'http://localhost:8001/api/receipts/{receipt_id}')
                if get_response.status_code == 200:
                    receipt_data = get_response.json()
                    extracted = receipt_data.get('extracted_data', {})
                    print(f"\n📄 Processed Receipt Data:")
                    print(f"   Vendor: {extracted.get('vendor_name', 'N/A')}")
                    print(f"   Amount: ${extracted.get('total_amount', 'N/A')}")
                    print(f"   Category: {receipt_data.get('category', 'N/A')}")
                    print(f"   Confidence: {receipt_data.get('confidence_score', 'N/A')}")
                else:
                    print(f"❌ Could not retrieve receipt: {get_response.status_code}")
            
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error text: {response.text}")
            return False
            
    finally:
        # Clean up
        os.unlink(image_path)

if __name__ == "__main__":
    test_upload()