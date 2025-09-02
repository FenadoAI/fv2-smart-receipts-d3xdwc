import os
import json
import io
import logging
from typing import Dict, Any, Optional, List
from PIL import Image
import pytesseract
import cv2
import numpy as np
from pdf2image import convert_from_bytes
import openai
import anthropic
from datetime import datetime
import re
from dataclasses import dataclass
import magic

logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    text: str
    confidence: float
    bounding_boxes: List[Dict]

class AIReceiptProcessor:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
    async def process_receipt(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """Main processing pipeline for receipts"""
        try:
            # Step 1: Extract text using OCR
            ocr_result = await self.extract_text_ocr(file_path, mime_type)
            
            # Step 2: Extract structured data using AI
            extracted_data = await self.extract_structured_data(ocr_result.text)
            
            # Step 3: Categorize the receipt
            category = await self.categorize_receipt(extracted_data, ocr_result.text)
            
            # Step 4: Calculate confidence score
            confidence_score = self.calculate_confidence_score(ocr_result, extracted_data)
            
            return {
                "extracted_data": extracted_data,
                "category": category,
                "confidence_score": confidence_score,
                "manual_review_needed": confidence_score < 0.8,
                "raw_text": ocr_result.text
            }
        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}")
            raise
    
    async def extract_text_ocr(self, file_path: str, mime_type: str) -> OCRResult:
        """Extract text from receipt image using OCR"""
        try:
            if mime_type.startswith('image/'):
                # Process image file
                image = Image.open(file_path)
                # Preprocess image for better OCR results
                processed_image = self.preprocess_image(image)
                
                # Extract text with bounding boxes
                data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
                text = pytesseract.image_to_string(processed_image)
                
                # Calculate average confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                # Extract bounding boxes for high-confidence text
                bounding_boxes = []
                for i in range(len(data['text'])):
                    if int(data['conf'][i]) > 60:  # Only include high-confidence text
                        bounding_boxes.append({
                            'text': data['text'][i],
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i],
                            'confidence': data['conf'][i]
                        })
                
                return OCRResult(
                    text=text,
                    confidence=avg_confidence / 100.0,
                    bounding_boxes=bounding_boxes
                )
                
            elif mime_type == 'application/pdf':
                # Convert PDF to images and process
                with open(file_path, 'rb') as pdf_file:
                    images = convert_from_bytes(pdf_file.read())
                
                all_text = []
                all_boxes = []
                total_confidence = 0
                
                for image in images:
                    processed_image = self.preprocess_image(image)
                    text = pytesseract.image_to_string(processed_image)
                    data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
                    
                    all_text.append(text)
                    
                    # Extract bounding boxes
                    for i in range(len(data['text'])):
                        if int(data['conf'][i]) > 60:
                            all_boxes.append({
                                'text': data['text'][i],
                                'x': data['left'][i],
                                'y': data['top'][i],
                                'width': data['width'][i],
                                'height': data['height'][i],
                                'confidence': data['conf'][i]
                            })
                    
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    if confidences:
                        total_confidence += sum(confidences) / len(confidences)
                
                avg_confidence = total_confidence / len(images) if images else 0
                
                return OCRResult(
                    text='\n'.join(all_text),
                    confidence=avg_confidence / 100.0,
                    bounding_boxes=all_boxes
                )
            else:
                raise ValueError(f"Unsupported file type: {mime_type}")
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert PIL Image to OpenCV format
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_cv = img_array
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY) if len(img_cv.shape) == 3 else img_cv
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Convert back to PIL Image
        return Image.fromarray(thresh)
    
    async def extract_structured_data(self, raw_text: str) -> Dict[str, Any]:
        """Extract structured data from raw text using AI"""
        try:
            prompt = f"""
            Extract the following information from this receipt text. Return the response as a JSON object:

            Receipt text:
            {raw_text}

            Please extract:
            - vendor_name: The business/store name
            - total_amount: Total amount paid (number only)
            - tax_amount: Tax amount if available (number only)
            - date: Date of purchase (ISO format YYYY-MM-DD)
            - description: Brief description of the purchase
            - line_items: Array of items with description and price
            - payment_method: How it was paid (cash, card, etc.)
            - receipt_number: Receipt or transaction number

            Return only valid JSON. If a field cannot be determined, use null.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured data from receipts. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            
            # Clean up the response and parse JSON
            result = result.strip()
            if result.startswith('```json'):
                result = result[7:]
            if result.endswith('```'):
                result = result[:-3]
            
            parsed_data = json.loads(result)
            
            # Convert date string to datetime if present
            if parsed_data.get('date'):
                try:
                    parsed_data['date'] = datetime.fromisoformat(parsed_data['date'])
                except:
                    parsed_data['date'] = None
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}")
            # Fallback to regex-based extraction
            return self.fallback_extraction(raw_text)
    
    def fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback extraction using regex patterns"""
        result = {
            "vendor_name": None,
            "total_amount": None,
            "tax_amount": None,
            "date": None,
            "description": None,
            "line_items": [],
            "payment_method": None,
            "receipt_number": None
        }
        
        # Extract total amount patterns
        total_patterns = [
            r'(?:total|amount due|balance)[:\s]*\$?(\d+\.?\d*)',
            r'\$(\d+\.\d{2})\s*(?:total|due)',
            r'(?:grand total|final total)[:\s]*\$?(\d+\.?\d*)'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["total_amount"] = float(match.group(1))
                break
        
        # Extract date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{2,4}[/-]\d{1,2}[/-]\d{1,2})',
            r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Simple date parsing - would need more robust parsing in production
                    date_str = match.group(1)
                    result["date"] = datetime.now()  # Placeholder
                    break
                except:
                    continue
        
        return result
    
    async def categorize_receipt(self, extracted_data: Dict[str, Any], raw_text: str) -> str:
        """Categorize the receipt using AI"""
        try:
            vendor = extracted_data.get('vendor_name', '')
            description = extracted_data.get('description', '')
            items = extracted_data.get('line_items', [])
            
            context = f"""
            Vendor: {vendor}
            Description: {description}
            Items: {items}
            Raw text sample: {raw_text[:500]}
            """
            
            prompt = f"""
            Based on this receipt information, categorize it into one of these categories:
            - office_supplies
            - meals_entertainment
            - travel
            - fuel
            - equipment
            - professional_services
            - utilities
            - rent
            - marketing
            - software
            - other

            Receipt information:
            {context}

            Return only the category name, nothing else.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at categorizing business expenses. Return only the category name."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            category = response.choices[0].message.content.strip().lower()
            
            # Validate category
            valid_categories = [
                "office_supplies", "meals_entertainment", "travel", "fuel", 
                "equipment", "professional_services", "utilities", "rent", 
                "marketing", "software", "other"
            ]
            
            return category if category in valid_categories else "other"
            
        except Exception as e:
            logger.error(f"Categorization failed: {str(e)}")
            return "other"
    
    def calculate_confidence_score(self, ocr_result: OCRResult, extracted_data: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the extraction"""
        scores = []
        
        # OCR confidence
        scores.append(ocr_result.confidence)
        
        # Data completeness score
        essential_fields = ['vendor_name', 'total_amount', 'date']
        completed_fields = sum(1 for field in essential_fields if extracted_data.get(field) is not None)
        completeness_score = completed_fields / len(essential_fields)
        scores.append(completeness_score)
        
        # Data quality score (e.g., realistic amounts, valid dates)
        quality_score = 1.0
        if extracted_data.get('total_amount'):
            if extracted_data['total_amount'] <= 0 or extracted_data['total_amount'] > 10000:
                quality_score -= 0.3
        
        scores.append(quality_score)
        
        # Return weighted average
        weights = [0.4, 0.4, 0.2]  # OCR, completeness, quality
        return sum(score * weight for score, weight in zip(scores, weights))

# Initialize the processor
ai_processor = AIReceiptProcessor()