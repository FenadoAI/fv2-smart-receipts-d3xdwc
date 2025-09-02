from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json
from enum import Enum

# Setup
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="Receiptor AI", description="Intelligent Receipt Management System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize security
security = HTTPBearer()

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory storage for demo (replace with real database)
receipts_db = {}
rules_db = {}
integrations_db = {}
audit_log_db = []

# Define Enums
class ReceiptCategory(str, Enum):
    OFFICE_SUPPLIES = "office_supplies"
    MEALS_ENTERTAINMENT = "meals_entertainment"
    TRAVEL = "travel"
    FUEL = "fuel"
    EQUIPMENT = "equipment"
    PROFESSIONAL_SERVICES = "professional_services"
    UTILITIES = "utilities"
    RENT = "rent"
    MARKETING = "marketing"
    SOFTWARE = "software"
    OTHER = "other"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class IntegrationType(str, Enum):
    XERO = "xero"
    QUICKBOOKS = "quickbooks"

# Define Models
class ExtractedData(BaseModel):
    vendor_name: Optional[str] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    line_items: List[Dict[str, Any]] = []
    payment_method: Optional[str] = None
    receipt_number: Optional[str] = None

class Receipt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    extracted_data: Optional[ExtractedData] = None
    category: Optional[ReceiptCategory] = None
    confidence_score: Optional[float] = None
    manual_review_needed: bool = False
    sync_status: Dict[str, bool] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

class ReceiptCreate(BaseModel):
    user_id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str

class ReceiptUpdate(BaseModel):
    category: Optional[ReceiptCategory] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    extracted_data: Optional[ExtractedData] = None

class AIRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AIRuleCreate(BaseModel):
    user_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]

# Helper functions
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Simple mock authentication - replace with proper JWT validation
    return "user123"  # Mock user ID

def mock_ai_processing(file_path: str, mime_type: str) -> Dict[str, Any]:
    """Mock AI processing function"""
    return {
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
        "manual_review_needed": False
    }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Receiptor AI - Intelligent Receipt Management System"}

@api_router.post("/receipts/upload", response_model=Receipt)
async def upload_receipt(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """Upload and process a receipt"""
    try:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        unique_filename = f"{file_id}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Create receipt record
        receipt = Receipt(
            user_id=user_id,
            filename=file.filename,
            file_path=str(file_path),
            file_size=len(content),
            mime_type=file.content_type,
            processing_status=ProcessingStatus.PENDING
        )
        
        # Store in memory database
        receipts_db[receipt.id] = receipt
        
        # Mock AI processing
        try:
            receipt.processing_status = ProcessingStatus.PROCESSING
            
            # Process with mock AI
            ai_result = mock_ai_processing(str(file_path), file.content_type)
            
            # Update receipt with AI results
            receipt.extracted_data = ExtractedData(**ai_result["extracted_data"])
            receipt.category = ai_result["category"]
            receipt.confidence_score = ai_result["confidence_score"]
            receipt.manual_review_needed = ai_result["manual_review_needed"]
            receipt.processing_status = ProcessingStatus.COMPLETED
            
            # Update in database
            receipts_db[receipt.id] = receipt
            
            # Log audit event
            audit_log_db.append({
                "event_type": "receipt_uploaded",
                "user_id": user_id,
                "timestamp": datetime.utcnow(),
                "resource_id": receipt.id,
                "details": {
                    "filename": file.filename,
                    "file_size": len(content),
                    "mime_type": file.content_type
                }
            })
            
        except Exception as e:
            logger.error(f"AI processing failed: {str(e)}")
            receipt.processing_status = ProcessingStatus.FAILED
            receipts_db[receipt.id] = receipt
        
        return receipt
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Upload failed")

@api_router.get("/receipts", response_model=List[Receipt])
async def get_receipts(
    user_id: str = Depends(get_current_user),
    category: Optional[ReceiptCategory] = None,
    status: Optional[ProcessingStatus] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get user's receipts with optional filtering"""
    user_receipts = [r for r in receipts_db.values() if r.user_id == user_id]
    
    if category:
        user_receipts = [r for r in user_receipts if r.category == category]
    if status:
        user_receipts = [r for r in user_receipts if r.processing_status == status]
    
    # Apply pagination
    return user_receipts[offset:offset + limit]

@api_router.get("/receipts/{receipt_id}", response_model=Receipt)
async def get_receipt(
    receipt_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get a specific receipt"""
    if receipt_id not in receipts_db:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    receipt = receipts_db[receipt_id]
    if receipt.user_id != user_id:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    return receipt

@api_router.put("/receipts/{receipt_id}", response_model=Receipt)
async def update_receipt(
    receipt_id: str,
    update_data: ReceiptUpdate,
    user_id: str = Depends(get_current_user)
):
    """Update receipt information"""
    if receipt_id not in receipts_db:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    receipt = receipts_db[receipt_id]
    if receipt.user_id != user_id:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Update fields
    if update_data.category is not None:
        receipt.category = update_data.category
    if update_data.tags is not None:
        receipt.tags = update_data.tags
    if update_data.notes is not None:
        receipt.notes = update_data.notes
    if update_data.extracted_data is not None:
        receipt.extracted_data = update_data.extracted_data
    
    receipts_db[receipt_id] = receipt
    return receipt

@api_router.delete("/receipts/{receipt_id}")
async def delete_receipt(
    receipt_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a receipt"""
    if receipt_id not in receipts_db:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    receipt = receipts_db[receipt_id]
    if receipt.user_id != user_id:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Delete file
    try:
        os.remove(receipt.file_path)
    except:
        pass  # File might already be deleted
    
    # Delete from database
    del receipts_db[receipt_id]
    
    return {"message": "Receipt deleted successfully"}

# AI Rules endpoints
@api_router.post("/ai-rules", response_model=AIRule)
async def create_ai_rule(
    rule_data: AIRuleCreate,
    user_id: str = Depends(get_current_user)
):
    """Create an AI processing rule"""
    rule = AIRule(**rule_data.dict())
    rules_db[rule.id] = rule
    return rule

@api_router.get("/ai-rules", response_model=List[AIRule])
async def get_ai_rules(user_id: str = Depends(get_current_user)):
    """Get user's AI rules"""
    return [rule for rule in rules_db.values() if rule.user_id == user_id]

# Analytics endpoints
@api_router.get("/analytics/summary")
async def get_analytics_summary(user_id: str = Depends(get_current_user)):
    """Get receipt analytics summary"""
    user_receipts = [r for r in receipts_db.values() if r.user_id == user_id]
    
    total_receipts = len(user_receipts)
    total_amount = sum(
        r.extracted_data.total_amount or 0 
        for r in user_receipts 
        if r.extracted_data and r.extracted_data.total_amount
    )
    
    # Category breakdown
    category_stats = {}
    for receipt in user_receipts:
        if receipt.category and receipt.extracted_data and receipt.extracted_data.total_amount:
            if receipt.category not in category_stats:
                category_stats[receipt.category] = {"count": 0, "total_amount": 0}
            category_stats[receipt.category]["count"] += 1
            category_stats[receipt.category]["total_amount"] += receipt.extracted_data.total_amount
    
    category_breakdown = [
        {"_id": category, **stats} 
        for category, stats in category_stats.items()
    ]
    
    return {
        "total_receipts": total_receipts,
        "total_amount": total_amount,
        "category_breakdown": category_breakdown,
        "monthly_trends": []  # Simplified for demo
    }

# Audit trail
@api_router.get("/audit/trail")
async def get_audit_trail(
    user_id: str = Depends(get_current_user),
    limit: int = 100
):
    """Get audit trail"""
    user_events = [
        event for event in audit_log_db 
        if event.get("user_id") == user_id
    ]
    return {
        "events": user_events[-limit:],
        "count": len(user_events)
    }

# Include the router in the main app
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)