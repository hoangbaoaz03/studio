
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_registration():
    url = f"{BASE_URL}/auth/register/"
    payload = {
        "username": "auth_test_user",
        "email": "authtest@example.com",
        "password": "SecurePassword123!",
        "password2": "SecurePassword123!",
        "first_name": "Auth",
        "last_name": "Test"
    }
    print(f"Testing Registration at {url}...")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201:
            print("✅ Registration Successful")
            return True, payload
        elif response.status_code == 400 and "username" in response.json() and "already exists" in str(response.json()):
            print("⚠️ User already exists, proceeding to login...")
            return True, payload
        else:
            print(f"❌ Registration Failed: {response.status_code} - {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False, None

def test_login(username, password):
    url = f"{BASE_URL}/token/"
    payload = {
        "username": username,
        "password": password
    }
    print(f"Testing Login at {url}...")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Login Successful")
            tokens = response.json()
            if "access" in tokens and "refresh" in tokens:
                print("✅ Tokens received")
                return tokens['access']
            else:
                print("❌ tokens missing from response")
                return None
        else:
            print(f"❌ Login Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def test_me(token):
    url = f"{BASE_URL}/auth/me/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    print(f"Testing Me Endpoint at {url}...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"✅ Me Endpoint Successful: {response.json().get('username')}")
            return True
        else:
            print(f"❌ Me Endpoint Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def main():
    print("=== STARTING BACKEND AUTH VERIFICATION ===")
    success, user_data = test_registration()
    if not success:
        sys.exit(1)
    
    token = test_login(user_data['username'], user_data['password'])
    if not token:
        sys.exit(1)
        
    if not test_me(token):
        sys.exit(1)
        
    print("=== ALL CHECKS PASSED ===")

if __name__ == "__main__":
    main()
