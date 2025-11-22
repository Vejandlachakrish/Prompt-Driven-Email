import json
import os
from datetime import datetime
from typing import List, Dict, Any
from fixed.models.email_models import EmailCreate

def load_mock_emails() -> List[Dict[str, Any]]:
    """Load mock emails from JSON file"""
    mock_file_path = os.path.join(os.path.dirname(__file__), 'mock_emails.json')
    
    try:
        with open(mock_file_path, 'r', encoding='utf-8') as f:
            emails = json.load(f)
        
        # Convert date strings to datetime objects
        for email in emails:
            if isinstance(email.get('date'), str):
                email['date'] = datetime.fromisoformat(email['date'])
        
        return emails
    except Exception as e:
        print(f"Error loading mock emails: {e}")
        return []

def get_sample_emails() -> List[EmailCreate]:
    """Get sample emails as EmailCreate objects"""
    mock_emails = load_mock_emails()
    email_objects = []
    
    for email_data in mock_emails:
        try:
            email = EmailCreate(
                sender=email_data['sender'],
                recipient=email_data['recipient'],
                subject=email_data['subject'],
                body=email_data['body'],
                date=email_data['date'],
                message_id=email_data['message_id']
            )
            email_objects.append(email)
        except Exception as e:
            print(f"Error creating email object: {e}")
            continue
    
    return email_objects

def initialize_mock_data(db_manager) -> int:
    """Initialize database with mock data"""
    try:
        sample_emails = get_sample_emails()
        added_count = 0
        
        for email in sample_emails:
            if db_manager.add_email(email):
                added_count += 1
        
        print(f"Successfully added {added_count} mock emails to database")
        return added_count
        
    except Exception as e:
        print(f"Error initializing mock data: {e}")
        return 0