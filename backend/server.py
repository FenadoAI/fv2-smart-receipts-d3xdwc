from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
try:
    import aiofiles
except ImportError:
    # Mock aiofiles for testing without full dependencies
    class MockAiofiles:
        @staticmethod
        async def open(file_path, mode='rb'):
            class MockFile:
                def __init__(self, path, mode):
                    self.path = path
                    self.mode = mode
                
                async def write(self, data):
                    with open(self.path, self.mode) as f:
                        f.write(data)
                
                async def __aenter__(self):
                    return self
                
                async def __aexit__(self, *args):
                    pass
            
            return MockFile(file_path, mode)
    
    aiofiles = MockAiofiles()

import json
from enum import Enum

# Mock aiofiles for environments without it
try:
    import aiofiles
except ImportError:
    class MockAiofiles:
        @staticmethod
        def open(file_path, mode):
            return open(file_path, mode.replace('b', ''))
    aiofiles = MockAiofiles()


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


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
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

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

class IntegrationConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    integration_type: IntegrationType
    config_data: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_sync: Optional[datetime] = None

class IntegrationConfigCreate(BaseModel):
    user_id: str
    integration_type: IntegrationType
    config_data: Dict[str, Any]

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    subscription_tier: str = "free"

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

# Initialize security
security = HTTPBearer()

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Import AI service (use mock for testing)
try:
    from ai_service import ai_processor
    ai_service_type = "full"
except ImportError:
    from ai_service_mock import ai_processor
    ai_service_type = "mock"

try:
    from integrations import integration_manager
    integration_type = "full"
except ImportError:
    from integrations_mock import integration_manager
    integration_type = "mock"
from ai_rules_engine import get_rules_engine
from compliance import (
    get_audit_logger, 
    get_retention_manager, 
    get_compliance_reporter,
    compliance_validator,
    AuditEventType
)

# Helper functions
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Simple mock authentication - replace with proper JWT validation
    return "user123"  # Mock user ID

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Receiptor AI - Intelligent Receipt Management"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Receipt management endpoints
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
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create receipt record
        receipt = Receipt(
            user_id=user_id,
            filename=file.filename,
            file_path=str(file_path),
            file_size=len(content),
            mime_type=file.content_type,
            processing_status=ProcessingStatus.PENDING
        )
        
        # Save to database
        await db.receipts.insert_one(receipt.dict())
        
        # Log audit event
        audit_logger = get_audit_logger(db)
        await audit_logger.log_event(
            AuditEventType.RECEIPT_UPLOADED,
            user_id,
            {
                "filename": file.filename,
                "file_size": len(content),
                "mime_type": file.content_type
            },
            resource_id=receipt.id,
            resource_type="receipt"
        )
        
        # Start AI processing (in background)
        try:
            receipt.processing_status = ProcessingStatus.PROCESSING
            await db.receipts.update_one(
                {"id": receipt.id},
                {"$set": {"processing_status": receipt.processing_status}}
            )
            
            # Process with AI
            ai_result = await ai_processor.process_receipt(str(file_path), file.content_type)
            
            # Update receipt with AI results
            receipt.extracted_data = ExtractedData(**ai_result["extracted_data"])
            receipt.category = ai_result["category"]
            receipt.confidence_score = ai_result["confidence_score"]
            receipt.manual_review_needed = ai_result["manual_review_needed"]
            receipt.processing_status = ProcessingStatus.COMPLETED
            
            # Update in database
            await db.receipts.update_one(
                {"id": receipt.id},
                {"$set": receipt.dict()}
            )
            
            # Apply AI rules
            try:
                rules_engine = get_rules_engine(db)
                rule_matches = await rules_engine.process_receipt(receipt.dict())
                
                if rule_matches:
                    logger.info(f"Applied {len(rule_matches)} rules to receipt {receipt.id}")
                    
                    # Store rule applications
                    await db.receipt_rule_applications.insert_many([
                        {
                            "receipt_id": receipt.id,
                            "rule_id": match.rule_id,
                            "rule_name": match.rule_name,
                            "confidence": match.confidence,
                            "actions_applied": match.actions_applied,
                            "applied_at": datetime.utcnow()
                        }
                        for match in rule_matches
                    ])
                    
            except Exception as e:
                logger.error(f"Failed to apply AI rules: {str(e)}")
            
        except Exception as e:
            logger.error(f"AI processing failed: {str(e)}")
            receipt.processing_status = ProcessingStatus.FAILED
            await db.receipts.update_one(
                {"id": receipt.id},
                {"$set": {"processing_status": receipt.processing_status}}
            )
        
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
    query = {"user_id": user_id}
    
    if category:
        query["category"] = category
    if status:
        query["processing_status"] = status
    
    receipts = await db.receipts.find(query).skip(offset).limit(limit).to_list(limit)
    return [Receipt(**receipt) for receipt in receipts]

@api_router.get("/receipts/{receipt_id}", response_model=Receipt)
async def get_receipt(
    receipt_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get a specific receipt"""
    receipt = await db.receipts.find_one({"id": receipt_id, "user_id": user_id})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return Receipt(**receipt)

@api_router.put("/receipts/{receipt_id}", response_model=Receipt)
async def update_receipt(
    receipt_id: str,
    update_data: ReceiptUpdate,
    user_id: str = Depends(get_current_user)
):
    """Update receipt information"""
    receipt = await db.receipts.find_one({"id": receipt_id, "user_id": user_id})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    
    if update_dict:
        await db.receipts.update_one(
            {"id": receipt_id},
            {"$set": update_dict}
        )
        
        # Get updated receipt
        updated_receipt = await db.receipts.find_one({"id": receipt_id})
        return Receipt(**updated_receipt)
    
    return Receipt(**receipt)

@api_router.delete("/receipts/{receipt_id}")
async def delete_receipt(
    receipt_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a receipt"""
    receipt = await db.receipts.find_one({"id": receipt_id, "user_id": user_id})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Delete file
    try:
        os.remove(receipt["file_path"])
    except:
        pass  # File might already be deleted
    
    # Delete from database
    await db.receipts.delete_one({"id": receipt_id})
    
    return {"message": "Receipt deleted successfully"}

# AI Rules endpoints
@api_router.post("/ai-rules", response_model=AIRule)
async def create_ai_rule(
    rule_data: AIRuleCreate,
    user_id: str = Depends(get_current_user)
):
    """Create an AI processing rule"""
    rule = AIRule(**rule_data.dict())
    await db.ai_rules.insert_one(rule.dict())
    return rule

@api_router.get("/ai-rules", response_model=List[AIRule])
async def get_ai_rules(user_id: str = Depends(get_current_user)):
    """Get user's AI rules"""
    rules = await db.ai_rules.find({"user_id": user_id}).to_list(100)
    return [AIRule(**rule) for rule in rules]

@api_router.put("/ai-rules/{rule_id}", response_model=AIRule)
async def update_ai_rule(
    rule_id: str,
    rule_data: AIRuleCreate,
    user_id: str = Depends(get_current_user)
):
    """Update an AI rule"""
    rule = await db.ai_rules.find_one({"id": rule_id, "user_id": user_id})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    update_data = rule_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.ai_rules.update_one(
        {"id": rule_id},
        {"$set": update_data}
    )
    
    updated_rule = await db.ai_rules.find_one({"id": rule_id})
    return AIRule(**updated_rule)

@api_router.delete("/ai-rules/{rule_id}")
async def delete_ai_rule(
    rule_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete an AI rule"""
    rule = await db.ai_rules.find_one({"id": rule_id, "user_id": user_id})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    await db.ai_rules.delete_one({"id": rule_id})
    return {"message": "AI rule deleted successfully"}

@api_router.post("/ai-rules/{rule_id}/test")
async def test_ai_rule(
    rule_id: str,
    user_id: str = Depends(get_current_user)
):
    """Test an AI rule against recent receipts"""
    rule = await db.ai_rules.find_one({"id": rule_id, "user_id": user_id})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Get recent receipts to test against
    recent_receipts = await db.receipts.find({"user_id": user_id}).limit(10).to_list(10)
    
    rules_engine = get_rules_engine(db)
    test_results = []
    
    for receipt in recent_receipts:
        try:
            # Temporarily set rule as the only active rule
            original_rule = dict(rule)
            matches = await rules_engine._evaluate_rule(original_rule, receipt)
            
            test_results.append({
                "receipt_id": receipt["id"],
                "filename": receipt["filename"],
                "vendor_name": receipt.get("extracted_data", {}).get("vendor_name"),
                "matched": matches is not None,
                "confidence": matches.confidence if matches else 0,
                "actions_would_apply": matches.actions_applied if matches else []
            })
            
        except Exception as e:
            test_results.append({
                "receipt_id": receipt["id"],
                "filename": receipt["filename"],
                "error": str(e)
            })
    
    return {
        "rule_id": rule_id,
        "rule_name": rule["name"],
        "test_results": test_results,
        "total_tested": len(test_results),
        "total_matched": sum(1 for r in test_results if r.get("matched", False))
    }

@api_router.get("/ai-rules/suggestions")
async def get_rule_suggestions(user_id: str = Depends(get_current_user)):
    """Get AI rule suggestions based on user's receipt patterns"""
    rules_engine = get_rules_engine(db)
    suggestions = await rules_engine.get_rule_suggestions(user_id)
    
    return {
        "suggestions": suggestions,
        "count": len(suggestions)
    }

@api_router.post("/receipts/{receipt_id}/apply-rules")
async def apply_rules_to_receipt(
    receipt_id: str,
    user_id: str = Depends(get_current_user)
):
    """Manually apply AI rules to a specific receipt"""
    receipt = await db.receipts.find_one({"id": receipt_id, "user_id": user_id})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    rules_engine = get_rules_engine(db)
    rule_matches = await rules_engine.process_receipt(receipt)
    
    if rule_matches:
        # Store rule applications
        await db.receipt_rule_applications.insert_many([
            {
                "receipt_id": receipt_id,
                "rule_id": match.rule_id,
                "rule_name": match.rule_name,
                "confidence": match.confidence,
                "actions_applied": match.actions_applied,
                "applied_at": datetime.utcnow()
            }
            for match in rule_matches
        ])
    
    return {
        "receipt_id": receipt_id,
        "rules_applied": len(rule_matches),
        "matches": [
            {
                "rule_name": match.rule_name,
                "confidence": match.confidence,
                "actions_applied": match.actions_applied
            }
            for match in rule_matches
        ]
    }

@api_router.get("/receipts/{receipt_id}/rule-history")
async def get_receipt_rule_history(
    receipt_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get AI rule application history for a receipt"""
    receipt = await db.receipts.find_one({"id": receipt_id, "user_id": user_id})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    applications = await db.receipt_rule_applications.find({"receipt_id": receipt_id}).to_list(100)
    
    return {
        "receipt_id": receipt_id,
        "rule_applications": applications
    }

# Analytics endpoints
@api_router.get("/analytics/summary")
async def get_analytics_summary(user_id: str = Depends(get_current_user)):
    """Get receipt analytics summary"""
    total_receipts = await db.receipts.count_documents({"user_id": user_id})
    
    # Get receipts by category
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}, "total_amount": {"$sum": "$extracted_data.total_amount"}}}
    ]
    category_stats = await db.receipts.aggregate(pipeline).to_list(100)
    
    # Get monthly totals
    monthly_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": {
                "year": {"$year": "$upload_timestamp"},
                "month": {"$month": "$upload_timestamp"}
            },
            "count": {"$sum": 1},
            "total_amount": {"$sum": "$extracted_data.total_amount"}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    monthly_stats = await db.receipts.aggregate(monthly_pipeline).to_list(100)
    
    return {
        "total_receipts": total_receipts,
        "category_breakdown": category_stats,
        "monthly_trends": monthly_stats
    }

# Integration endpoints
@api_router.post("/integrations", response_model=IntegrationConfig)
async def create_integration(
    integration_data: IntegrationConfigCreate,
    user_id: str = Depends(get_current_user)
):
    """Configure a new accounting integration"""
    try:
        # Test the integration
        success = integration_manager.add_integration(
            integration_data.integration_type,
            integration_data.config_data
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Invalid integration configuration")
        
        # Test connection
        connection_ok = await integration_manager.test_connection(integration_data.integration_type)
        if not connection_ok:
            raise HTTPException(status_code=400, detail="Failed to connect to integration")
        
        # Save configuration
        integration = IntegrationConfig(**integration_data.dict())
        await db.integrations.insert_one(integration.dict())
        
        return integration
        
    except Exception as e:
        logger.error(f"Integration setup failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Integration setup failed")

@api_router.get("/integrations", response_model=List[IntegrationConfig])
async def get_integrations(user_id: str = Depends(get_current_user)):
    """Get user's configured integrations"""
    integrations = await db.integrations.find({"user_id": user_id}).to_list(100)
    return [IntegrationConfig(**integration) for integration in integrations]

@api_router.put("/integrations/{integration_id}", response_model=IntegrationConfig)
async def update_integration(
    integration_id: str,
    integration_data: IntegrationConfigCreate,
    user_id: str = Depends(get_current_user)
):
    """Update an integration configuration"""
    integration = await db.integrations.find_one({"id": integration_id, "user_id": user_id})
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Test the updated configuration
    success = integration_manager.add_integration(
        integration_data.integration_type,
        integration_data.config_data
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid integration configuration")
    
    update_data = integration_data.dict()
    await db.integrations.update_one(
        {"id": integration_id},
        {"$set": update_data}
    )
    
    updated_integration = await db.integrations.find_one({"id": integration_id})
    return IntegrationConfig(**updated_integration)

@api_router.delete("/integrations/{integration_id}")
async def delete_integration(
    integration_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete an integration"""
    integration = await db.integrations.find_one({"id": integration_id, "user_id": user_id})
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    await db.integrations.delete_one({"id": integration_id})
    return {"message": "Integration deleted successfully"}

@api_router.post("/integrations/{integration_id}/test")
async def test_integration(
    integration_id: str,
    user_id: str = Depends(get_current_user)
):
    """Test an integration connection"""
    integration = await db.integrations.find_one({"id": integration_id, "user_id": user_id})
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Add integration to manager
    success = integration_manager.add_integration(
        integration["integration_type"],
        integration["config_data"]
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to initialize integration")
    
    # Test connection
    connection_ok = await integration_manager.test_connection(integration["integration_type"])
    
    return {
        "success": connection_ok,
        "message": "Connection successful" if connection_ok else "Connection failed"
    }

@api_router.post("/receipts/{receipt_id}/sync")
async def sync_receipt(
    receipt_id: str,
    user_id: str = Depends(get_current_user)
):
    """Sync a receipt to all configured integrations"""
    receipt = await db.receipts.find_one({"id": receipt_id, "user_id": user_id})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Get user's integrations
    integrations = await db.integrations.find({"user_id": user_id, "is_active": True}).to_list(100)
    
    if not integrations:
        raise HTTPException(status_code=400, detail="No active integrations found")
    
    # Add integrations to manager
    for integration in integrations:
        integration_manager.add_integration(
            integration["integration_type"],
            integration["config_data"]
        )
    
    # Sync receipt
    sync_results = await integration_manager.sync_receipt_to_all(receipt)
    
    # Update receipt sync status
    sync_status = {
        integration["integration_type"]: result["success"]
        for integration, result in zip(integrations, sync_results.values())
    }
    
    await db.receipts.update_one(
        {"id": receipt_id},
        {"$set": {"sync_status": sync_status}}
    )
    
    return {
        "receipt_id": receipt_id,
        "sync_results": sync_results
    }

@api_router.post("/receipts/sync-all")
async def sync_all_receipts(user_id: str = Depends(get_current_user)):
    """Sync all unsynced receipts to configured integrations"""
    # Get user's integrations
    integrations = await db.integrations.find({"user_id": user_id, "is_active": True}).to_list(100)
    
    if not integrations:
        raise HTTPException(status_code=400, detail="No active integrations found")
    
    # Add integrations to manager
    for integration in integrations:
        integration_manager.add_integration(
            integration["integration_type"],
            integration["config_data"]
        )
    
    # Get unsynced receipts
    unsynced_receipts = await db.receipts.find({
        "user_id": user_id,
        "processing_status": "completed",
        "$or": [
            {"sync_status": {"$exists": False}},
            {"sync_status": {}}
        ]
    }).to_list(1000)
    
    sync_results = []
    
    for receipt in unsynced_receipts:
        try:
            result = await integration_manager.sync_receipt_to_all(receipt)
            
            # Update receipt sync status
            sync_status = {
                integration["integration_type"]: result.get(integration["integration_type"], {}).get("success", False)
                for integration in integrations
            }
            
            await db.receipts.update_one(
                {"id": receipt["id"]},
                {"$set": {"sync_status": sync_status}}
            )
            
            sync_results.append({
                "receipt_id": receipt["id"],
                "filename": receipt["filename"],
                "results": result
            })
            
        except Exception as e:
            logger.error(f"Failed to sync receipt {receipt['id']}: {str(e)}")
            sync_results.append({
                "receipt_id": receipt["id"],
                "filename": receipt["filename"],
                "error": str(e)
            })
    
    return {
        "synced_count": len(sync_results),
        "results": sync_results
    }

# Compliance and audit endpoints
@api_router.get("/compliance/validate/{receipt_id}")
async def validate_receipt_compliance(
    receipt_id: str,
    user_id: str = Depends(get_current_user)
):
    """Validate a receipt for compliance requirements"""
    receipt = await db.receipts.find_one({"id": receipt_id, "user_id": user_id})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Validate completeness
    completeness_validation = compliance_validator.validate_receipt_completeness(receipt)
    
    # Validate tax requirements
    tax_validation = compliance_validator.validate_tax_requirements(receipt)
    
    return {
        "receipt_id": receipt_id,
        "completeness_validation": completeness_validation,
        "tax_validation": tax_validation,
        "overall_compliant": completeness_validation['is_compliant'] and tax_validation['is_compliant']
    }

@api_router.get("/compliance/report")
async def generate_compliance_report(
    start_date: str,
    end_date: str,
    user_id: str = Depends(get_current_user)
):
    """Generate compliance report for a date range"""
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD)")
    
    compliance_reporter = get_compliance_reporter(db)
    report = await compliance_reporter.generate_compliance_report(user_id, start_dt, end_dt)
    
    # Log audit event
    audit_logger = get_audit_logger(db)
    await audit_logger.log_event(
        AuditEventType.EXPORT_GENERATED,
        user_id,
        {
            "report_type": "compliance",
            "start_date": start_date,
            "end_date": end_date,
            "total_receipts": report['summary']['total_receipts']
        }
    )
    
    return report

@api_router.get("/audit/trail")
async def get_audit_trail(
    user_id: str = Depends(get_current_user),
    resource_id: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """Get audit trail with optional filters"""
    filters = {}
    
    if resource_id:
        filters['resource_id'] = resource_id
    if event_type:
        try:
            filters['event_type'] = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid event type")
    
    if start_date:
        try:
            filters['start_date'] = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            filters['end_date'] = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    audit_logger = get_audit_logger(db)
    events = await audit_logger.get_audit_trail(
        user_id=user_id,
        limit=limit,
        **filters
    )
    
    return {
        "events": events,
        "count": len(events),
        "filters_applied": filters
    }

@api_router.post("/audit/verify/{event_id}")
async def verify_audit_event(
    event_id: str,
    user_id: str = Depends(get_current_user)
):
    """Verify the integrity of an audit event"""
    audit_logger = get_audit_logger(db)
    is_valid = await audit_logger.verify_data_integrity(event_id)
    
    return {
        "event_id": event_id,
        "is_valid": is_valid,
        "verified_at": datetime.utcnow()
    }

@api_router.get("/compliance/retention-status")
async def get_retention_status(user_id: str = Depends(get_current_user)):
    """Get data retention status"""
    retention_manager = get_retention_manager(db)
    status = await retention_manager.get_retention_status()
    
    return {
        "retention_status": status,
        "checked_at": datetime.utcnow()
    }

@api_router.post("/compliance/apply-retention")
async def apply_retention_policy(
    data_type: str,
    user_id: str = Depends(get_current_user)
):
    """Apply retention policy for specific data type"""
    allowed_types = ['receipts', 'audit_log', 'temporary_files']
    
    if data_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid data type. Allowed: {', '.join(allowed_types)}"
        )
    
    retention_manager = get_retention_manager(db)
    result = await retention_manager.apply_retention_policy(data_type)
    
    # Log audit event
    audit_logger = get_audit_logger(db)
    await audit_logger.log_event(
        AuditEventType.EXPORT_GENERATED,  # Using this as closest match
        user_id,
        {
            "action": "retention_policy_applied",
            "data_type": data_type,
            "deleted_count": result['deleted_count'],
            "archived_count": result['archived_count']
        }
    )
    
    return result

@api_router.get("/compliance/export/receipts")
async def export_receipts_for_compliance(
    format: str = "csv",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Export receipts in compliance format"""
    query = {"user_id": user_id}
    
    # Add date filters
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = datetime.fromisoformat(start_date)
        if end_date:
            date_filter["$lte"] = datetime.fromisoformat(end_date)
        query["upload_timestamp"] = date_filter
    
    if category:
        query["category"] = category
    
    receipts = await db.receipts.find(query).to_list(10000)
    
    # Format for export
    export_data = []
    for receipt in receipts:
        extracted_data = receipt.get('extracted_data', {})
        export_data.append({
            'Receipt ID': receipt['id'],
            'Upload Date': receipt['upload_timestamp'].isoformat() if receipt.get('upload_timestamp') else '',
            'Receipt Date': extracted_data.get('date', ''),
            'Vendor': extracted_data.get('vendor_name', ''),
            'Description': extracted_data.get('description', ''),
            'Total Amount': extracted_data.get('total_amount', 0),
            'Tax Amount': extracted_data.get('tax_amount', 0),
            'Category': receipt.get('category', ''),
            'Receipt Number': extracted_data.get('receipt_number', ''),
            'Payment Method': extracted_data.get('payment_method', ''),
            'Filename': receipt['filename'],
            'Processing Status': receipt.get('processing_status', ''),
            'Manual Review Needed': receipt.get('manual_review_needed', False),
            'Confidence Score': receipt.get('confidence_score', 0),
            'Tags': ', '.join(receipt.get('tags', [])),
            'Notes': receipt.get('notes', '')
        })
    
    # Log audit event
    audit_logger = get_audit_logger(db)
    await audit_logger.log_event(
        AuditEventType.EXPORT_GENERATED,
        user_id,
        {
            "export_type": "receipts",
            "format": format,
            "record_count": len(export_data),
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "category": category
            }
        }
    )
    
    return {
        "export_data": export_data,
        "record_count": len(export_data),
        "format": format,
        "generated_at": datetime.utcnow()
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
