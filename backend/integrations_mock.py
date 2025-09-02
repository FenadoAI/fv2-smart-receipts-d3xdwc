"""
Mock integrations for testing without external dependencies
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MockIntegrationManager:
    """Mock integration manager for testing"""
    
    def __init__(self):
        self.integrations = {}
    
    def add_integration(self, integration_type: str, config: Dict[str, Any]) -> bool:
        """Mock add integration"""
        self.integrations[integration_type] = config
        return True
    
    async def sync_receipt_to_all(self, receipt_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Mock sync to all integrations"""
        results = {}
        for integration_type in self.integrations:
            results[integration_type] = {
                'success': True,
                'message': f'Successfully synced to {integration_type} (mock)',
                'external_id': f'mock_{integration_type}_{receipt_data.get("id", "unknown")}'
            }
        return results
    
    async def test_connection(self, integration_type: str) -> bool:
        """Mock connection test"""
        return integration_type in self.integrations

# Create mock instance
integration_manager = MockIntegrationManager()