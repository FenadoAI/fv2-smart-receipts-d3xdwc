import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class RuleMatch:
    rule_id: str
    rule_name: str
    confidence: float
    actions_applied: List[str]

class ConditionEvaluator:
    """Evaluates rule conditions against receipt data"""
    
    @staticmethod
    def evaluate_condition(condition: Dict[str, Any], receipt_data: Dict[str, Any]) -> bool:
        """Evaluate a single condition"""
        condition_type = condition.get('type')
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        # Get the actual value from receipt data
        actual_value = ConditionEvaluator._get_field_value(field, receipt_data)
        
        if actual_value is None:
            return False
        
        # Evaluate based on condition type
        if condition_type == 'text':
            return ConditionEvaluator._evaluate_text_condition(actual_value, operator, value)
        elif condition_type == 'number':
            return ConditionEvaluator._evaluate_number_condition(actual_value, operator, value)
        elif condition_type == 'date':
            return ConditionEvaluator._evaluate_date_condition(actual_value, operator, value)
        elif condition_type == 'boolean':
            return ConditionEvaluator._evaluate_boolean_condition(actual_value, operator, value)
        
        return False
    
    @staticmethod
    def _get_field_value(field_path: str, data: Dict[str, Any]) -> Any:
        """Get nested field value from receipt data"""
        try:
            keys = field_path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            
            return current
        except:
            return None
    
    @staticmethod
    def _evaluate_text_condition(actual: Any, operator: str, expected: str) -> bool:
        """Evaluate text-based conditions"""
        if actual is None:
            return False
        
        actual_str = str(actual).lower()
        expected_str = str(expected).lower()
        
        if operator == 'equals':
            return actual_str == expected_str
        elif operator == 'contains':
            return expected_str in actual_str
        elif operator == 'starts_with':
            return actual_str.startswith(expected_str)
        elif operator == 'ends_with':
            return actual_str.endswith(expected_str)
        elif operator == 'regex':
            try:
                return bool(re.search(expected_str, actual_str, re.IGNORECASE))
            except:
                return False
        elif operator == 'not_equals':
            return actual_str != expected_str
        elif operator == 'not_contains':
            return expected_str not in actual_str
        
        return False
    
    @staticmethod
    def _evaluate_number_condition(actual: Any, operator: str, expected: float) -> bool:
        """Evaluate number-based conditions"""
        try:
            actual_num = float(actual)
            expected_num = float(expected)
            
            if operator == 'equals':
                return actual_num == expected_num
            elif operator == 'greater_than':
                return actual_num > expected_num
            elif operator == 'less_than':
                return actual_num < expected_num
            elif operator == 'greater_than_or_equal':
                return actual_num >= expected_num
            elif operator == 'less_than_or_equal':
                return actual_num <= expected_num
            elif operator == 'not_equals':
                return actual_num != expected_num
            
        except (ValueError, TypeError):
            pass
        
        return False
    
    @staticmethod
    def _evaluate_date_condition(actual: Any, operator: str, expected: str) -> bool:
        """Evaluate date-based conditions"""
        try:
            if isinstance(actual, datetime):
                actual_date = actual
            else:
                actual_date = datetime.fromisoformat(str(actual))
            
            expected_date = datetime.fromisoformat(expected)
            
            if operator == 'equals':
                return actual_date.date() == expected_date.date()
            elif operator == 'after':
                return actual_date > expected_date
            elif operator == 'before':
                return actual_date < expected_date
            elif operator == 'on_or_after':
                return actual_date >= expected_date
            elif operator == 'on_or_before':
                return actual_date <= expected_date
            
        except (ValueError, TypeError):
            pass
        
        return False
    
    @staticmethod
    def _evaluate_boolean_condition(actual: Any, operator: str, expected: bool) -> bool:
        """Evaluate boolean conditions"""
        try:
            actual_bool = bool(actual)
            expected_bool = bool(expected)
            
            if operator == 'equals':
                return actual_bool == expected_bool
            elif operator == 'not_equals':
                return actual_bool != expected_bool
            
        except (ValueError, TypeError):
            pass
        
        return False

class ActionExecutor:
    """Executes rule actions on receipt data"""
    
    @staticmethod
    async def execute_actions(actions: Dict[str, Any], receipt_data: Dict[str, Any], db) -> List[str]:
        """Execute all actions for a rule"""
        executed_actions = []
        
        for action_type, action_config in actions.items():
            try:
                if action_type == 'set_category':
                    await ActionExecutor._set_category(action_config, receipt_data, db)
                    executed_actions.append(f"Set category to {action_config.get('category')}")
                
                elif action_type == 'add_tags':
                    await ActionExecutor._add_tags(action_config, receipt_data, db)
                    executed_actions.append(f"Added tags: {', '.join(action_config.get('tags', []))}")
                
                elif action_type == 'set_description':
                    await ActionExecutor._set_description(action_config, receipt_data, db)
                    executed_actions.append(f"Set description to {action_config.get('description')}")
                
                elif action_type == 'flag_for_review':
                    await ActionExecutor._flag_for_review(action_config, receipt_data, db)
                    executed_actions.append("Flagged for manual review")
                
                elif action_type == 'auto_sync':
                    await ActionExecutor._auto_sync(action_config, receipt_data, db)
                    executed_actions.append("Enabled auto-sync")
                
                elif action_type == 'set_account_code':
                    await ActionExecutor._set_account_code(action_config, receipt_data, db)
                    executed_actions.append(f"Set account code to {action_config.get('account_code')}")
                
                elif action_type == 'apply_tax_rule':
                    await ActionExecutor._apply_tax_rule(action_config, receipt_data, db)
                    executed_actions.append(f"Applied tax rule: {action_config.get('tax_rule')}")
                
            except Exception as e:
                logger.error(f"Failed to execute action {action_type}: {str(e)}")
        
        return executed_actions
    
    @staticmethod
    async def _set_category(config: Dict[str, Any], receipt_data: Dict[str, Any], db):
        """Set receipt category"""
        category = config.get('category')
        if category:
            await db.receipts.update_one(
                {"id": receipt_data["id"]},
                {"$set": {"category": category}}
            )
    
    @staticmethod
    async def _add_tags(config: Dict[str, Any], receipt_data: Dict[str, Any], db):
        """Add tags to receipt"""
        new_tags = config.get('tags', [])
        if new_tags:
            existing_tags = receipt_data.get('tags', [])
            combined_tags = list(set(existing_tags + new_tags))
            
            await db.receipts.update_one(
                {"id": receipt_data["id"]},
                {"$set": {"tags": combined_tags}}
            )
    
    @staticmethod
    async def _set_description(config: Dict[str, Any], receipt_data: Dict[str, Any], db):
        """Set custom description"""
        description = config.get('description')
        if description:
            # Support template variables
            template_vars = {
                'vendor_name': receipt_data.get('extracted_data', {}).get('vendor_name', ''),
                'amount': receipt_data.get('extracted_data', {}).get('total_amount', ''),
                'date': receipt_data.get('extracted_data', {}).get('date', ''),
                'category': receipt_data.get('category', '')
            }
            
            formatted_description = description.format(**template_vars)
            
            await db.receipts.update_one(
                {"id": receipt_data["id"]},
                {"$set": {"notes": formatted_description}}
            )
    
    @staticmethod
    async def _flag_for_review(config: Dict[str, Any], receipt_data: Dict[str, Any], db):
        """Flag receipt for manual review"""
        reason = config.get('reason', 'Triggered by AI rule')
        
        await db.receipts.update_one(
            {"id": receipt_data["id"]},
            {"$set": {
                "manual_review_needed": True,
                "review_reason": reason
            }}
        )
    
    @staticmethod
    async def _auto_sync(config: Dict[str, Any], receipt_data: Dict[str, Any], db):
        """Enable auto-sync for receipt"""
        await db.receipts.update_one(
            {"id": receipt_data["id"]},
            {"$set": {"auto_sync": True}}
        )
    
    @staticmethod
    async def _set_account_code(config: Dict[str, Any], receipt_data: Dict[str, Any], db):
        """Set accounting software account code"""
        account_code = config.get('account_code')
        if account_code:
            await db.receipts.update_one(
                {"id": receipt_data["id"]},
                {"$set": {"account_code": account_code}}
            )
    
    @staticmethod
    async def _apply_tax_rule(config: Dict[str, Any], receipt_data: Dict[str, Any], db):
        """Apply specific tax rule"""
        tax_rule = config.get('tax_rule')
        if tax_rule:
            await db.receipts.update_one(
                {"id": receipt_data["id"]},
                {"$set": {"tax_rule": tax_rule}}
            )

class RulesEngine:
    """Main AI rules engine for processing receipts"""
    
    def __init__(self, db):
        self.db = db
        self.condition_evaluator = ConditionEvaluator()
        self.action_executor = ActionExecutor()
    
    async def process_receipt(self, receipt_data: Dict[str, Any]) -> List[RuleMatch]:
        """Process a receipt against all applicable rules"""
        user_id = receipt_data.get('user_id')
        if not user_id:
            return []
        
        # Get active rules for the user
        rules = await self.db.ai_rules.find({
            "user_id": user_id,
            "is_active": True
        }).to_list(1000)
        
        matches = []
        
        for rule in rules:
            try:
                match = await self._evaluate_rule(rule, receipt_data)
                if match:
                    matches.append(match)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.get('id', 'unknown')}: {str(e)}")
        
        return matches
    
    async def _evaluate_rule(self, rule: Dict[str, Any], receipt_data: Dict[str, Any]) -> Optional[RuleMatch]:
        """Evaluate a single rule against receipt data"""
        conditions = rule.get('conditions', {})
        
        # Evaluate all conditions
        if not self._evaluate_conditions(conditions, receipt_data):
            return None
        
        # Execute actions
        actions = rule.get('actions', {})
        executed_actions = await self.action_executor.execute_actions(actions, receipt_data, self.db)
        
        # Calculate confidence based on condition matches
        confidence = self._calculate_confidence(conditions, receipt_data)
        
        # Update rule usage statistics
        await self._update_rule_stats(rule['id'])
        
        return RuleMatch(
            rule_id=rule['id'],
            rule_name=rule['name'],
            confidence=confidence,
            actions_applied=executed_actions
        )
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], receipt_data: Dict[str, Any]) -> bool:
        """Evaluate rule conditions with logical operators"""
        logic_operator = conditions.get('logic', 'AND')
        condition_list = conditions.get('conditions', [])
        
        if not condition_list:
            return False
        
        results = []
        for condition in condition_list:
            result = self.condition_evaluator.evaluate_condition(condition, receipt_data)
            results.append(result)
        
        if logic_operator == 'AND':
            return all(results)
        elif logic_operator == 'OR':
            return any(results)
        elif logic_operator == 'NOT':
            return not any(results)
        
        return False
    
    def _calculate_confidence(self, conditions: Dict[str, Any], receipt_data: Dict[str, Any]) -> float:
        """Calculate confidence score for rule match"""
        condition_list = conditions.get('conditions', [])
        if not condition_list:
            return 0.0
        
        matches = 0
        total = len(condition_list)
        
        for condition in condition_list:
            if self.condition_evaluator.evaluate_condition(condition, receipt_data):
                matches += 1
        
        return matches / total
    
    async def _update_rule_stats(self, rule_id: str):
        """Update rule usage statistics"""
        await self.db.ai_rules.update_one(
            {"id": rule_id},
            {
                "$inc": {"usage_count": 1},
                "$set": {"last_used": datetime.utcnow()}
            }
        )
    
    async def get_rule_suggestions(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate rule suggestions based on user's receipt patterns"""
        # Analyze user's receipts to suggest common patterns
        receipts = await self.db.receipts.find({"user_id": user_id}).to_list(1000)
        
        suggestions = []
        
        # Analyze vendor patterns
        vendor_frequency = {}
        category_patterns = {}
        
        for receipt in receipts:
            vendor = receipt.get('extracted_data', {}).get('vendor_name')
            category = receipt.get('category')
            
            if vendor:
                vendor_frequency[vendor] = vendor_frequency.get(vendor, 0) + 1
                if category:
                    if vendor not in category_patterns:
                        category_patterns[vendor] = {}
                    category_patterns[vendor][category] = category_patterns[vendor].get(category, 0) + 1
        
        # Suggest rules for frequent vendors
        for vendor, count in vendor_frequency.items():
            if count >= 3:  # At least 3 receipts from this vendor
                most_common_category = None
                if vendor in category_patterns:
                    most_common_category = max(category_patterns[vendor], key=category_patterns[vendor].get)
                
                if most_common_category:
                    suggestions.append({
                        "type": "vendor_categorization",
                        "title": f"Auto-categorize {vendor} receipts",
                        "description": f"Automatically categorize receipts from {vendor} as {most_common_category}",
                        "conditions": {
                            "logic": "AND",
                            "conditions": [{
                                "type": "text",
                                "field": "extracted_data.vendor_name",
                                "operator": "contains",
                                "value": vendor
                            }]
                        },
                        "actions": {
                            "set_category": {
                                "category": most_common_category
                            },
                            "add_tags": {
                                "tags": ["auto-categorized"]
                            }
                        }
                    })
        
        # Suggest amount-based rules
        high_amount_receipts = [r for r in receipts if r.get('extracted_data', {}).get('total_amount', 0) > 1000]
        if len(high_amount_receipts) > 0:
            suggestions.append({
                "type": "high_amount_review",
                "title": "Flag high-amount receipts for review",
                "description": "Automatically flag receipts over $1000 for manual review",
                "conditions": {
                    "logic": "AND",
                    "conditions": [{
                        "type": "number",
                        "field": "extracted_data.total_amount",
                        "operator": "greater_than",
                        "value": 1000
                    }]
                },
                "actions": {
                    "flag_for_review": {
                        "reason": "High amount - requires review"
                    },
                    "add_tags": {
                        "tags": ["high-amount", "review-required"]
                    }
                }
            })
        
        return suggestions

# Global rules engine instance
rules_engine = None

def get_rules_engine(db):
    """Get or create rules engine instance"""
    global rules_engine
    if rules_engine is None:
        rules_engine = RulesEngine(db)
    return rules_engine