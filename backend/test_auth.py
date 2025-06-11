import requests
import json
import time
from urllib3.exceptions import NewConnectionError

BASE_URL = "http://localhost:8000/api"

def wait_for_server(max_retries=5, delay=2):
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("Server is running!")
                return True
        except requests.exceptions.ConnectionError:
            print(f"Attempt {i+1}/{max_retries}: Waiting for server to start...")
            time.sleep(delay)
    return False

def test_register():
    url = f"{BASE_URL}/auth/register"
    data = {
        "email": "test@example.com",
        "password": "password123",
        "is_admin": False
    }
    try:
        response = requests.post(url, json=data)
        print("Register Response:", response.status_code)
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"Error during registration: {e}")

def test_login():
    url = f"{BASE_URL}/auth/login"
    data = {
        "email": "test@example.com",
        "password": "password123"
    }
    try:
        response = requests.post(url, json=data)
        print("\nLogin Response:", response.status_code)
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"Error during login: {e}")

if __name__ == "__main__":
    print("Waiting for server to start...")
    if wait_for_server():
        print("\nTesting registration...")
        test_register()
        print("\nTesting login...")
        test_login()
    else:
        print("Could not connect to server. Please make sure it's running on port 8000.") 