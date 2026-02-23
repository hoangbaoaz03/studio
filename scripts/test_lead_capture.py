
import requests
import json
import sys

# API Endpoint (adjust port if needed, usually 8000 for Django)
URL = "http://localhost:8000/api/business/leads/"

def test_create_lead():
    print(f"🚀 Testing Lead Capture API: {URL}")
    
    payload = {
        "full_name": "Test Demo User",
        "email": "demo_test@example.com",
        "company_name": "Demo Corp",
        "team_size": "51-200",
        "message": "I want a demo.",
        "request_type": "DEMO"
    }
    
    try:
        response = requests.post(URL, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: Lead created successfully!")
            return True
        else:
            print("❌ FAILURE: API did not return 201 Created.")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Could not connect to API. {e}")
        return False

if __name__ == "__main__":
    success = test_create_lead()
    if not success:
        sys.exit(1)
