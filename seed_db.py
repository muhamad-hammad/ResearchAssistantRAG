import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def seed_db():
    email = "test@example.com"
    password = "password123"
    
    print("1. Logging in...")
    login_data = {"username": email, "password": password}
    req = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    if req.status_code != 200:
        print(f"Failed to login: {req.text}")
        sys.exit(1)
        
    token = req.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("2. Uploading test paper...")
    with open("test_paper.pdf", "rb") as f:
        files = {"file": ("test_paper.pdf", f, "application/pdf")}
        req = requests.post(f"{BASE_URL}/api/papers/upload", headers=headers, files=files)
        
        if req.status_code != 200:
            print(f"Failed to upload: {req.text}")
            sys.exit(1)
            
        paper_id = req.json()["id"]
        print(f"Uploaded successfully! Paper ID: {paper_id}")

    print("Polling status...")
    for _ in range(20):
        req = requests.get(f"{BASE_URL}/api/papers/{paper_id}/status", headers=headers)
        status = req.json()["status"]
        if status == "ready":
             print("Paper is READY!")
             sys.exit(0)
        print(f"Wait... status is {status}")
        time.sleep(3)
    
    print("Paper processing took too long or failed.")
    sys.exit(1)

if __name__ == "__main__":
    seed_db()
