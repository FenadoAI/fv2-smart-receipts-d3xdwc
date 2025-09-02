from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import uuid
import json
from datetime import datetime

app = FastAPI(title="Receiptor AI", description="Simple Receipt Management API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
receipts_store: Dict[str, Dict] = {}
categories = [
    "office_supplies", "meals_entertainment", "travel", "fuel", 
    "equipment", "professional_services", "utilities", "rent", 
    "marketing", "software", "other"
]

def mock_ai_processing(filename: str) -> Dict[str, Any]:
    """Mock AI processing that returns realistic data"""
    mock_data = {
        "vendor_name": "Starbucks Coffee" if "starbucks" in filename.lower() else "Business Vendor",
        "total_amount": 15.50,
        "tax_amount": 1.24,
        "date": datetime.now().isoformat(),
        "description": "Business expense",
        "receipt_number": f"REC-{uuid.uuid4().hex[:8].upper()}"
    }
    
    # Simple category assignment
    if "starbucks" in filename.lower() or "coffee" in filename.lower():
        category = "meals_entertainment"
    elif "gas" in filename.lower() or "fuel" in filename.lower():
        category = "fuel"
    elif "office" in filename.lower():
        category = "office_supplies"
    else:
        category = "other"
    
    return {
        "extracted_data": mock_data,
        "category": category,
        "confidence_score": 0.95
    }

@app.get("/")
async def root():
    return {"message": "Receiptor AI - Simple Receipt Management"}

@app.post("/api/receipts/upload")
async def upload_receipt(file: UploadFile = File(...)):
    """Upload and process a receipt"""
    try:
        # Generate receipt ID
        receipt_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Mock AI processing
        ai_result = mock_ai_processing(file.filename)
        
        # Create receipt record
        receipt = {
            "id": receipt_id,
            "filename": file.filename,
            "file_size": len(content),
            "mime_type": file.content_type,
            "upload_timestamp": datetime.now().isoformat(),
            "processing_status": "completed",
            "extracted_data": ai_result["extracted_data"],
            "category": ai_result["category"],
            "confidence_score": ai_result["confidence_score"],
            "manual_review_needed": ai_result["confidence_score"] < 0.8
        }
        
        # Store receipt
        receipts_store[receipt_id] = receipt
        
        return receipt
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/receipts")
async def get_receipts(category: str = None, limit: int = 100):
    """Get all receipts with optional filtering"""
    receipts = list(receipts_store.values())
    
    if category:
        receipts = [r for r in receipts if r.get("category") == category]
    
    # Sort by upload time (newest first)
    receipts.sort(key=lambda x: x["upload_timestamp"], reverse=True)
    
    return receipts[:limit]

@app.get("/api/receipts/{receipt_id}")
async def get_receipt(receipt_id: str):
    """Get a specific receipt"""
    if receipt_id not in receipts_store:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    return receipts_store[receipt_id]

@app.put("/api/receipts/{receipt_id}")
async def update_receipt(receipt_id: str, update_data: Dict[str, Any]):
    """Update receipt information"""
    if receipt_id not in receipts_store:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    receipt = receipts_store[receipt_id]
    
    # Update allowed fields
    if "category" in update_data:
        receipt["category"] = update_data["category"]
    if "notes" in update_data:
        receipt["notes"] = update_data["notes"]
    if "tags" in update_data:
        receipt["tags"] = update_data["tags"]
    
    receipts_store[receipt_id] = receipt
    return receipt

@app.delete("/api/receipts/{receipt_id}")
async def delete_receipt(receipt_id: str):
    """Delete a receipt"""
    if receipt_id not in receipts_store:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    del receipts_store[receipt_id]
    return {"message": "Receipt deleted successfully"}

@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get receipt analytics summary"""
    receipts = list(receipts_store.values())
    
    total_receipts = len(receipts)
    total_amount = sum(r.get("extracted_data", {}).get("total_amount", 0) for r in receipts)
    
    # Category breakdown
    category_breakdown = {}
    for receipt in receipts:
        category = receipt.get("category", "other")
        amount = receipt.get("extracted_data", {}).get("total_amount", 0)
        
        if category not in category_breakdown:
            category_breakdown[category] = {"count": 0, "total_amount": 0}
        
        category_breakdown[category]["count"] += 1
        category_breakdown[category]["total_amount"] += amount
    
    # Convert to list format
    category_list = [
        {
            "_id": category,
            "count": data["count"],
            "total_amount": data["total_amount"]
        }
        for category, data in category_breakdown.items()
    ]
    
    return {
        "total_receipts": total_receipts,
        "total_amount": total_amount,
        "category_breakdown": category_list,
        "monthly_trends": []  # Simplified - no monthly trends
    }

@app.get("/api/categories")
async def get_categories():
    """Get available categories"""
    return {"categories": categories}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)