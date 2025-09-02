"""
Mock AI service for testing without heavy dependencies
"""
import logging
from typing import Dict, Any
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class MockAIReceiptProcessor:
    """Mock AI processor for testing"""
    
    async def process_receipt(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """Mock processing that returns realistic test data"""
        try:
            # Simulate processing delay
            import asyncio
            await asyncio.sleep(0.5)
            
            # Return mock extracted data
            mock_data = {
                "extracted_data": {
                    "vendor_name": "Starbucks Coffee",
                    "total_amount": 9.83,
                    "tax_amount": 0.73,
                    "date": datetime.now(),
                    "description": "Coffee and pastry purchase",
                    "line_items": [
                        {"description": "Grande Latte", "amount": 5.65},
                        {"description": "Blueberry Muffin", "amount": 3.45}
                    ],
                    "payment_method": "Credit Card",
                    "receipt_number": "1234567890"
                },
                "category": "meals_entertainment",
                "confidence_score": 0.95,
                "manual_review_needed": False,
                "raw_text": "STARBUCKS COFFEE\n123 Main Street\nDate: 2024-01-15\nGrande Latte $5.65\nBlueberry Muffin $3.45\nTotal: $9.83"
            }
            
            # Add some randomness to make it more realistic
            confidence = random.uniform(0.8, 0.98)
            mock_data["confidence_score"] = confidence
            mock_data["manual_review_needed"] = confidence < 0.85
            
            return mock_data
            
        except Exception as e:
            logger.error(f"Mock processing failed: {str(e)}")
            raise

# Create mock instance
ai_processor = MockAIReceiptProcessor()