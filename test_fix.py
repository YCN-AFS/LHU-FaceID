"""Quick test to check if API is working."""
import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing API endpoints...")

# Test 1: Health check
print("\n1. Testing /health...")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Verify_face (should fail without image)
print("\n2. Testing /verify_face (should fail without image)...")
try:
    response = requests.post(f"{BASE_URL}/verify_face")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Register_face (should fail without image)
print("\n3. Testing /register_face (should fail without image)...")
try:
    url = f"{BASE_URL}/register_face"
    params = {"student_id": "TEST", "name": "Test", "class_name": "K50"}
    response = requests.post(url, params=params)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

print("\nDone!")









