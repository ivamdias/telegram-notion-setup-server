import requests
import logging

logger = logging.getLogger(__name__)

class NotionAPIHelper:
    """Helper class for Notion API operations"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    def test_connection(self):
        """Test if the access token is valid"""
        try:
            response = requests.get("https://api.notion.com/v1/users/me", headers=self.headers)
            return response.status_code == 200, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            logger.error(f"Error testing Notion connection: {e}")
            return False, str(e)
    
    def get_database_info(self, database_id):
        """Get information about a specific database"""
        try:
            response = requests.get(f"https://api.notion.com/v1/databases/{database_id}", headers=self.headers)
            return response.status_code == 200, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return False, str(e)
    
    def create_test_page(self, database_id):
        """Create a test page in the database to verify write access"""
        try:
            data = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": "🧪 Setup Test - You can delete this"}}]
                    }
                }
            }
            
            response = requests.post("https://api.notion.com/v1/pages", headers=self.headers, json=data)
            return response.status_code == 200, response.json() if response.status_code == 200 else response.text
        except Exception as e:
            logger.error(f"Error creating test page: {e}")
            return False, str(e)

def validate_database_schema(database_info):
    """Validate that the database has the required properties"""
    required_properties = {
        'Name': 'title',
        'Start at': 'date', 
        'Finish at': 'date',
        'Priority': 'multi_select',
        'Progress': 'status'
    }
    
    properties = database_info.get('properties', {})
    missing_properties = []
    incorrect_types = []
    
    for prop_name, expected_type in required_properties.items():
        if prop_name not in properties:
            missing_properties.append(prop_name)
        elif properties[prop_name].get('type') != expected_type:
            incorrect_types.append(f"{prop_name} (expected: {expected_type}, found: {properties[prop_name].get('type')})")
    
    return missing_properties, incorrect_types
