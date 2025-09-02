import os
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import base64

logger = logging.getLogger(__name__)

class BaseIntegration(ABC):
    """Base class for accounting software integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = httpx.AsyncClient()
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the service"""
        pass
    
    @abstractmethod
    async def sync_receipt(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync a receipt to the accounting software"""
        pass
    
    @abstractmethod
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get chart of accounts"""
        pass
    
    @abstractmethod
    async def get_tax_rates(self) -> List[Dict[str, Any]]:
        """Get available tax rates"""
        pass

class XeroIntegration(BaseIntegration):
    """Xero accounting software integration"""
    
    BASE_URL = "https://api.xero.com/api.xro/2.0"
    AUTH_URL = "https://identity.xero.com/connect/token"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.access_token = config.get('access_token')
        self.refresh_token = config.get('refresh_token')
        self.tenant_id = config.get('tenant_id')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
    
    async def authenticate(self) -> bool:
        """Refresh access token using refresh token"""
        try:
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
            
            response = await self.client.post(self.AUTH_URL, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.refresh_token = token_data.get('refresh_token', self.refresh_token)
                return True
            else:
                logger.error(f"Xero authentication failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Xero authentication error: {str(e)}")
            return False
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make authenticated request to Xero API"""
        if not self.access_token:
            if not await self.authenticate():
                return None
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Xero-tenant-id': self.tenant_id,
            'Content-Type': 'application/json'
        }
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = await self.client.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = await self.client.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = await self.client.put(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == 401:
                # Token expired, try to refresh
                if await self.authenticate():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    if method.upper() == 'GET':
                        response = await self.client.get(url, headers=headers)
                    elif method.upper() == 'POST':
                        response = await self.client.post(url, headers=headers, json=data)
                    elif method.upper() == 'PUT':
                        response = await self.client.put(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Xero API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Xero API request error: {str(e)}")
            return None
    
    async def sync_receipt(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync receipt as expense claim or bill to Xero"""
        try:
            extracted_data = receipt_data.get('extracted_data', {})
            
            # Create expense claim
            expense_data = {
                "ExpenseClaims": [{
                    "User": {
                        "UserID": self.config.get('default_user_id')
                    },
                    "Receipts": [{
                        "ReceiptNumber": extracted_data.get('receipt_number', f"REC-{receipt_data['id'][:8]}"),
                        "Date": extracted_data.get('date', datetime.now().isoformat()[:10]),
                        "Contact": {
                            "Name": extracted_data.get('vendor_name', 'Unknown Vendor')
                        },
                        "Total": extracted_data.get('total_amount', 0),
                        "LineItems": [{
                            "Description": extracted_data.get('description', 'Expense'),
                            "Quantity": 1,
                            "UnitAmount": extracted_data.get('total_amount', 0),
                            "AccountCode": self._get_account_code(receipt_data.get('category', 'other')),
                            "TaxType": "INPUT"
                        }]
                    }]
                }]
            }
            
            result = await self._make_request('POST', 'ExpenseClaims', expense_data)
            
            if result and 'ExpenseClaims' in result:
                return {
                    'success': True,
                    'xero_id': result['ExpenseClaims'][0]['ExpenseClaimID'],
                    'message': 'Successfully synced to Xero'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to sync to Xero'
                }
                
        except Exception as e:
            logger.error(f"Xero sync error: {str(e)}")
            return {
                'success': False,
                'message': f'Sync error: {str(e)}'
            }
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get chart of accounts from Xero"""
        result = await self._make_request('GET', 'Accounts')
        if result and 'Accounts' in result:
            return result['Accounts']
        return []
    
    async def get_tax_rates(self) -> List[Dict[str, Any]]:
        """Get tax rates from Xero"""
        result = await self._make_request('GET', 'TaxRates')
        if result and 'TaxRates' in result:
            return result['TaxRates']
        return []
    
    def _get_account_code(self, category: str) -> str:
        """Map receipt category to Xero account code"""
        mapping = {
            'office_supplies': '404',  # Office Expenses
            'meals_entertainment': '420',  # Entertainment
            'travel': '493',  # Travel Expenses
            'fuel': '445',  # Motor Vehicle Expenses
            'equipment': '610',  # Equipment
            'professional_services': '425',  # Professional Fees
            'utilities': '445',  # Utilities
            'rent': '469',  # Rent
            'marketing': '400',  # Advertising
            'software': '404',  # Office Expenses
            'other': '404'  # Office Expenses (default)
        }
        return mapping.get(category, '404')

class QuickBooksIntegration(BaseIntegration):
    """QuickBooks Online integration"""
    
    BASE_URL = "https://sandbox-quickbooks.api.intuit.com"  # Use production URL for live
    AUTH_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.access_token = config.get('access_token')
        self.refresh_token = config.get('refresh_token')
        self.company_id = config.get('company_id')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
    
    async def authenticate(self) -> bool:
        """Refresh access token using refresh token"""
        try:
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
            
            response = await self.client.post(self.AUTH_URL, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.refresh_token = token_data.get('refresh_token', self.refresh_token)
                return True
            else:
                logger.error(f"QuickBooks authentication failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"QuickBooks authentication error: {str(e)}")
            return False
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make authenticated request to QuickBooks API"""
        if not self.access_token:
            if not await self.authenticate():
                return None
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.BASE_URL}/v3/company/{self.company_id}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = await self.client.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = await self.client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == 401:
                # Token expired, try to refresh
                if await self.authenticate():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    if method.upper() == 'GET':
                        response = await self.client.get(url, headers=headers)
                    elif method.upper() == 'POST':
                        response = await self.client.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"QuickBooks API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"QuickBooks API request error: {str(e)}")
            return None
    
    async def sync_receipt(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync receipt as expense to QuickBooks"""
        try:
            extracted_data = receipt_data.get('extracted_data', {})
            
            # Create expense
            expense_data = {
                "Purchase": {
                    "PaymentType": "Cash",
                    "AccountRef": {
                        "value": self._get_account_ref(receipt_data.get('category', 'other'))
                    },
                    "TxnDate": extracted_data.get('date', datetime.now().isoformat()[:10]),
                    "TotalAmt": extracted_data.get('total_amount', 0),
                    "Line": [{
                        "Amount": extracted_data.get('total_amount', 0),
                        "DetailType": "AccountBasedExpenseLineDetail",
                        "AccountBasedExpenseLineDetail": {
                            "AccountRef": {
                                "value": self._get_account_ref(receipt_data.get('category', 'other'))
                            }
                        }
                    }]
                }
            }
            
            # Add vendor if available
            if extracted_data.get('vendor_name'):
                vendor = await self._find_or_create_vendor(extracted_data['vendor_name'])
                if vendor:
                    expense_data["Purchase"]["EntityRef"] = {
                        "value": vendor['Id']
                    }
            
            result = await self._make_request('POST', 'purchase', expense_data)
            
            if result and 'QueryResponse' in result:
                return {
                    'success': True,
                    'qbo_id': result['QueryResponse']['Purchase'][0]['Id'],
                    'message': 'Successfully synced to QuickBooks'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to sync to QuickBooks'
                }
                
        except Exception as e:
            logger.error(f"QuickBooks sync error: {str(e)}")
            return {
                'success': False,
                'message': f'Sync error: {str(e)}'
            }
    
    async def _find_or_create_vendor(self, vendor_name: str) -> Optional[Dict]:
        """Find existing vendor or create new one"""
        # First try to find existing vendor
        result = await self._make_request('GET', f"vendors?query=Name='{vendor_name}'")
        
        if result and 'QueryResponse' in result and result['QueryResponse'].get('Vendor'):
            return result['QueryResponse']['Vendor'][0]
        
        # Create new vendor
        vendor_data = {
            "Vendor": {
                "Name": vendor_name
            }
        }
        
        result = await self._make_request('POST', 'vendor', vendor_data)
        if result and 'QueryResponse' in result:
            return result['QueryResponse']['Vendor'][0]
        
        return None
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get chart of accounts from QuickBooks"""
        result = await self._make_request('GET', 'accounts')
        if result and 'QueryResponse' in result:
            return result['QueryResponse'].get('Account', [])
        return []
    
    async def get_tax_rates(self) -> List[Dict[str, Any]]:
        """Get tax codes from QuickBooks"""
        result = await self._make_request('GET', 'taxcodes')
        if result and 'QueryResponse' in result:
            return result['QueryResponse'].get('TaxCode', [])
        return []
    
    def _get_account_ref(self, category: str) -> str:
        """Map receipt category to QuickBooks account reference"""
        # These would need to be configured based on the actual chart of accounts
        mapping = {
            'office_supplies': '25',  # Office Supplies
            'meals_entertainment': '26',  # Meals & Entertainment
            'travel': '27',  # Travel
            'fuel': '28',  # Auto Expenses
            'equipment': '29',  # Equipment
            'professional_services': '30',  # Professional Services
            'utilities': '31',  # Utilities
            'rent': '32',  # Rent
            'marketing': '33',  # Marketing
            'software': '34',  # Software
            'other': '35'  # Other Expenses
        }
        return mapping.get(category, '35')

class IntegrationManager:
    """Manages multiple accounting integrations"""
    
    def __init__(self):
        self.integrations: Dict[str, BaseIntegration] = {}
    
    def add_integration(self, integration_type: str, config: Dict[str, Any]) -> bool:
        """Add a new integration"""
        try:
            if integration_type == 'xero':
                self.integrations[integration_type] = XeroIntegration(config)
            elif integration_type == 'quickbooks':
                self.integrations[integration_type] = QuickBooksIntegration(config)
            else:
                logger.error(f"Unsupported integration type: {integration_type}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to add {integration_type} integration: {str(e)}")
            return False
    
    async def sync_receipt_to_all(self, receipt_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Sync receipt to all configured integrations"""
        results = {}
        
        for integration_type, integration in self.integrations.items():
            try:
                result = await integration.sync_receipt(receipt_data)
                results[integration_type] = result
            except Exception as e:
                logger.error(f"Failed to sync to {integration_type}: {str(e)}")
                results[integration_type] = {
                    'success': False,
                    'message': f'Sync failed: {str(e)}'
                }
        
        return results
    
    async def test_connection(self, integration_type: str) -> bool:
        """Test connection to an integration"""
        if integration_type not in self.integrations:
            return False
        
        try:
            return await self.integrations[integration_type].authenticate()
        except Exception as e:
            logger.error(f"Connection test failed for {integration_type}: {str(e)}")
            return False

# Global integration manager instance
integration_manager = IntegrationManager()