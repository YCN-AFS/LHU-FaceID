"""
Test script for LHU FaceID API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_register_face(student_id, name, class_name, image_path):
    """Test register face endpoint."""
    print(f"\n[TEST] Registering student: {student_id}")
    
    url = f"{BASE_URL}/register_face"
    params = {
        "student_id": student_id,
        "name": name,
        "class_name": class_name
    }
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, params=params, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_verify_face(image_path):
    """Test verify face endpoint."""
    print(f"\n[TEST] Verifying face from: {image_path}")
    
    url = f"{BASE_URL}/verify_face"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_get_student_info(student_id):
    """Test get student info endpoint."""
    print(f"\n[TEST] Getting info for student: {student_id}")
    
    url = f"{BASE_URL}/get_student_info/{student_id}"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_health():
    """Test health check endpoint."""
    print(f"\n[TEST] Health check")
    
    url = f"{BASE_URL}/health"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== LHU FaceID API Test Suite ===\n")
    
    # Test health check
    test_health()
    
    # Example usage (uncomment and provide actual image paths):
    # test_register_face("S001", "Nguyen Van A", "K50", "student_photo.jpg")
    # test_verify_face("face_to_verify.jpg")
    # test_get_student_info("S001")
    
    print("\n=== Test completed ===")

