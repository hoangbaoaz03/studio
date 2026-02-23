import requests

# First, login to get token
login_url = "http://localhost:8000/api/token/"
login_data = {"username": "instructor", "password": "password123"}

print("Logging in...")
login_response = requests.post(login_url, json=login_data)
print(f"Login status: {login_response.status_code}")

if login_response.status_code == 200:
    tokens = login_response.json()
    access_token = tokens['access']
    print(f"Got access token: {access_token[:50]}...")
    
    # Now try to fetch the draft course
    course_url = "http://localhost:8000/api/courses/courses/ai-for-newbie-1/"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"\nFetching course: {course_url}")
    course_response = requests.get(course_url, headers=headers)
    print(f"Course fetch status: {course_response.status_code}")
    print(f"Response: {course_response.text[:500] if course_response.text else 'No content'}")
else:
    print(f"Login failed: {login_response.text}")
