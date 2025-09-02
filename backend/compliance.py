import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib
import json
from enum import Enum

logger = logging.getLogger(__name__)

class AuditEventType(str, Enum):
    RECEIPT_UPLOADED = "receipt_uploaded"
    RECEIPT_UPDATED = "receipt_updated"
    RECEIPT_DELETED = "receipt_deleted"
    DATA_EXTRACTED = "data_extracted"
    CATEGORY_CHANGED = "category_changed"
    RULE_APPLIED = "rule_applied"
    SYNCED_TO_ACCOUNTING = "synced_to_accounting"
    MANUAL_REVIEW = "manual_review"
    EXPORT_GENERATED = "export_generated"
    USER_LOGIN = "user_login"
    INTEGRATION_CONFIGURED = "integration_configured"

@dataclass
class AuditEvent:
    event_id: str
    event_type: AuditEventType
    user_id: str
    timestamp: datetime
    resource_id: Optional[str]
    resource_type: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    data_hash: str

class ComplianceValidator:
    """Validates receipt data for compliance requirements"""
    
    def __init__(self):
        self.required_fields = [
            'vendor_name',
            'total_amount',
            'date',
            'description'
        ]
        
        self.tax_compliance_fields = [
            'tax_amount',
            'receipt_number'
        ]
    
    def validate_receipt_completeness(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate receipt data completeness for compliance"""
        validation_result = {
            'is_compliant': True,
            'missing_fields': [],
            'warnings': [],
            'score': 0.0
        }
        
        extracted_data = receipt_data.get('extracted_data', {})
        
        # Check required fields
        missing_required = []
        for field in self.required_fields:
            if not extracted_data.get(field):
                missing_required.append(field)
        
        validation_result['missing_fields'] = missing_required
        
        # Check tax compliance fields
        missing_tax_fields = []
        for field in self.tax_compliance_fields:
            if not extracted_data.get(field):
                missing_tax_fields.append(field)
        
        if missing_tax_fields:
            validation_result['warnings'].append(
                f"Missing tax compliance fields: {', '.join(missing_tax_fields)}"
            )
        
        # Calculate compliance score
        total_fields = len(self.required_fields) + len(self.tax_compliance_fields)
        present_fields = total_fields - len(missing_required) - len(missing_tax_fields)
        validation_result['score'] = present_fields / total_fields
        
        # Set compliance status
        validation_result['is_compliant'] = len(missing_required) == 0
        
        # Add specific warnings
        if not extracted_data.get('total_amount') or extracted_data.get('total_amount', 0) <= 0:
            validation_result['warnings'].append("Invalid or missing total amount")
        
        if extracted_data.get('date'):
            try:
                receipt_date = datetime.fromisoformat(str(extracted_data['date']))
                if receipt_date > datetime.now():
                    validation_result['warnings'].append("Receipt date is in the future")
                if receipt_date < datetime.now() - timedelta(days=2555):  # 7 years
                    validation_result['warnings'].append("Receipt is older than 7 years")
            except:
                validation_result['warnings'].append("Invalid receipt date format")
        
        return validation_result
    
    def validate_tax_requirements(self, receipt_data: Dict[str, Any], jurisdiction: str = "US") -> Dict[str, Any]:
        """Validate tax compliance requirements"""
        validation_result = {
            'is_compliant': True,
            'requirements_met': [],
            'requirements_failed': [],
            'recommendations': []
        }
        
        extracted_data = receipt_data.get('extracted_data', {})
        total_amount = extracted_data.get('total_amount', 0)
        
        if jurisdiction == "US":
            # IRS requirements
            if total_amount >= 75:  # IRS threshold for detailed receipts
                required_fields = ['vendor_name', 'total_amount', 'date', 'description']
                for field in required_fields:
                    if extracted_data.get(field):
                        validation_result['requirements_met'].append(f"Has {field}")
                    else:
                        validation_result['requirements_failed'].append(f"Missing {field}")
                
                # For meals and entertainment (50% deductible)
                if receipt_data.get('category') == 'meals_entertainment':
                    validation_result['recommendations'].append(
                        "Meals & Entertainment: Only 50% may be deductible. Ensure business purpose is documented."
                    )
                
                # For travel expenses
                if receipt_data.get('category') == 'travel':
                    validation_result['recommendations'].append(
                        "Travel expense: Document business purpose and destination."
                    )
            
            # Requirements for amounts over $2500
            if total_amount >= 2500:
                if not extracted_data.get('receipt_number'):
                    validation_result['requirements_failed'].append(
                        "Receipt number required for expenses over $2500"
                    )
                
                validation_result['recommendations'].append(
                    "High-value expense: Consider additional documentation for audit protection"
                )
        
        validation_result['is_compliant'] = len(validation_result['requirements_failed']) == 0
        
        return validation_result

class AuditLogger:
    """Handles audit logging for compliance"""
    
    def __init__(self, db):
        self.db = db
    
    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        details: Dict[str, Any],
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Log an audit event"""
        
        # Generate event ID
        event_id = self._generate_event_id(event_type, user_id, datetime.utcnow())
        
        # Create data hash for integrity
        data_hash = self._generate_data_hash(details)
        
        audit_event = {
            "event_id": event_id,
            "event_type": event_type,
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "resource_id": resource_id,
            "resource_type": resource_type,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "data_hash": data_hash
        }
        
        # Store in audit log collection
        await self.db.audit_log.insert_one(audit_event)
        
        logger.info(f"Audit event logged: {event_type} by user {user_id}")
        
        return event_id
    
    def _generate_event_id(self, event_type: AuditEventType, user_id: str, timestamp: datetime) -> str:
        """Generate unique event ID"""
        data = f"{event_type}_{user_id}_{timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _generate_data_hash(self, data: Dict[str, Any]) -> str:
        """Generate hash of event data for integrity verification"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    async def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail with filters"""
        
        query = {}
        
        if user_id:
            query["user_id"] = user_id
        if resource_id:
            query["resource_id"] = resource_id
        if event_type:
            query["event_type"] = event_type
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["timestamp"] = date_query
        
        events = await self.db.audit_log.find(query).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return events
    
    async def verify_data_integrity(self, event_id: str) -> bool:
        """Verify the integrity of an audit event"""
        event = await self.db.audit_log.find_one({"event_id": event_id})
        
        if not event:
            return False
        
        # Recalculate hash
        stored_hash = event.get("data_hash")
        calculated_hash = self._generate_data_hash(event.get("details", {}))
        
        return stored_hash == calculated_hash

class RetentionManager:
    """Manages data retention policies"""
    
    def __init__(self, db):
        self.db = db
        self.retention_periods = {
            'receipts': timedelta(days=2555),  # 7 years for tax purposes
            'audit_log': timedelta(days=2555),  # 7 years
            'user_data': timedelta(days=365),   # 1 year after account deletion
            'temporary_files': timedelta(days=30)  # 30 days
        }
    
    async def apply_retention_policy(self, data_type: str) -> Dict[str, Any]:
        """Apply retention policy for a specific data type"""
        
        if data_type not in self.retention_periods:
            raise ValueError(f"Unknown data type: {data_type}")
        
        retention_period = self.retention_periods[data_type]
        cutoff_date = datetime.utcnow() - retention_period
        
        result = {
            'data_type': data_type,
            'cutoff_date': cutoff_date,
            'deleted_count': 0,
            'archived_count': 0
        }
        
        if data_type == 'receipts':
            # For receipts, we might archive instead of delete
            old_receipts = await self.db.receipts.find({
                "upload_timestamp": {"$lt": cutoff_date}
            }).to_list(1000)
            
            if old_receipts:
                # Archive to separate collection
                await self.db.archived_receipts.insert_many(old_receipts)
                result['archived_count'] = len(old_receipts)
                
                # Delete from main collection
                delete_result = await self.db.receipts.delete_many({
                    "upload_timestamp": {"$lt": cutoff_date}
                })
                result['deleted_count'] = delete_result.deleted_count
        
        elif data_type == 'audit_log':
            # Audit logs should generally be archived, not deleted
            old_logs = await self.db.audit_log.find({
                "timestamp": {"$lt": cutoff_date}
            }).to_list(10000)
            
            if old_logs:
                await self.db.archived_audit_log.insert_many(old_logs)
                result['archived_count'] = len(old_logs)
        
        elif data_type == 'temporary_files':
            # Clean up old temporary files
            import os
            import glob
            
            temp_pattern = "/tmp/receiptor_*"
            for filepath in glob.glob(temp_pattern):
                try:
                    stat = os.stat(filepath)
                    file_age = datetime.utcnow() - datetime.fromtimestamp(stat.st_mtime)
                    
                    if file_age > retention_period:
                        os.remove(filepath)
                        result['deleted_count'] += 1
                except:
                    continue
        
        return result
    
    async def get_retention_status(self) -> Dict[str, Any]:
        """Get current retention status for all data types"""
        status = {}
        
        for data_type, retention_period in self.retention_periods.items():
            cutoff_date = datetime.utcnow() - retention_period
            
            if data_type == 'receipts':
                old_count = await self.db.receipts.count_documents({
                    "upload_timestamp": {"$lt": cutoff_date}
                })
                total_count = await self.db.receipts.count_documents({})
                
            elif data_type == 'audit_log':
                old_count = await self.db.audit_log.count_documents({
                    "timestamp": {"$lt": cutoff_date}
                })
                total_count = await self.db.audit_log.count_documents({})
            
            else:
                old_count = 0
                total_count = 0
            
            status[data_type] = {
                'retention_period_days': retention_period.days,
                'cutoff_date': cutoff_date,
                'items_eligible_for_cleanup': old_count,
                'total_items': total_count
            }
        
        return status

class ComplianceReporter:
    """Generates compliance reports"""
    
    def __init__(self, db):
        self.db = db
        self.validator = ComplianceValidator()
    
    async def generate_compliance_report(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        
        # Get receipts in date range
        receipts = await self.db.receipts.find({
            "user_id": user_id,
            "upload_timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).to_list(10000)
        
        report = {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_receipts': len(receipts),
                'total_amount': 0,
                'compliant_receipts': 0,
                'non_compliant_receipts': 0,
                'average_compliance_score': 0
            },
            'compliance_details': [],
            'category_breakdown': {},
            'issues_summary': {
                'missing_data': 0,
                'invalid_dates': 0,
                'high_amounts_no_detail': 0
            },
            'recommendations': []
        }
        
        compliance_scores = []
        category_totals = {}
        
        for receipt in receipts:
            # Validate compliance
            validation = self.validator.validate_receipt_completeness(receipt)
            tax_validation = self.validator.validate_tax_requirements(receipt)
            
            # Update summary
            total_amount = receipt.get('extracted_data', {}).get('total_amount', 0)
            report['summary']['total_amount'] += total_amount
            
            if validation['is_compliant'] and tax_validation['is_compliant']:
                report['summary']['compliant_receipts'] += 1
            else:
                report['summary']['non_compliant_receipts'] += 1
            
            compliance_scores.append(validation['score'])
            
            # Category breakdown
            category = receipt.get('category', 'uncategorized')
            if category not in category_totals:
                category_totals[category] = {'count': 0, 'amount': 0}
            category_totals[category]['count'] += 1
            category_totals[category]['amount'] += total_amount
            
            # Track issues
            if validation['missing_fields']:
                report['issues_summary']['missing_data'] += 1
            
            if 'Invalid receipt date' in validation.get('warnings', []):
                report['issues_summary']['invalid_dates'] += 1
            
            if total_amount > 1000 and len(validation['missing_fields']) > 0:
                report['issues_summary']['high_amounts_no_detail'] += 1
            
            # Add detailed compliance info
            report['compliance_details'].append({
                'receipt_id': receipt['id'],
                'filename': receipt['filename'],
                'amount': total_amount,
                'category': category,
                'compliance_score': validation['score'],
                'is_compliant': validation['is_compliant'] and tax_validation['is_compliant'],
                'issues': validation['missing_fields'] + validation.get('warnings', [])
            })
        
        # Calculate averages
        if compliance_scores:
            report['summary']['average_compliance_score'] = sum(compliance_scores) / len(compliance_scores)
        
        report['category_breakdown'] = category_totals
        
        # Generate recommendations
        if report['issues_summary']['missing_data'] > 0:
            report['recommendations'].append(
                f"Review {report['issues_summary']['missing_data']} receipts with missing required data"
            )
        
        if report['issues_summary']['high_amounts_no_detail'] > 0:
            report['recommendations'].append(
                f"Add details to {report['issues_summary']['high_amounts_no_detail']} high-value receipts"
            )
        
        if report['summary']['average_compliance_score'] < 0.8:
            report['recommendations'].append(
                "Overall compliance score is below 80%. Consider improving data capture processes."
            )
        
        return report

# Global instances
compliance_validator = ComplianceValidator()

def get_audit_logger(db):
    return AuditLogger(db)

def get_retention_manager(db):
    return RetentionManager(db)

def get_compliance_reporter(db):
    return ComplianceReporter(db)