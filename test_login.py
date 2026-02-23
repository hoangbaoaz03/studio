import requests

def test_login():
    url = "http://localhost:8000/api/token/"
    data = {
        "username": "instructor",
        "password": "password123"
    }
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Login Successful")
            print(response.json())
        else:
            print("Login Failed")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
