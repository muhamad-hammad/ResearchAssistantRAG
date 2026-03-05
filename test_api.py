import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_flow():
    print("1. Registering new user...")
    email = f"test_sprint5_{int(time.time())}@t.com"
    req = requests.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": "password"})
    
    if req.status_code != 200:
        print(f"Failed to register: {req.text}")
        sys.exit(1)
        
    print("2. Logging in...")
    login_data = {"username": email, "password": "password"}
    req = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    if req.status_code != 200:
        print(f"Failed to login: {req.text}")
        sys.exit(1)
        
    token = req.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("3. Uploading test paper...")
    # Make sure we have test_paper.pdf from earlier
    try:
        with open("test_paper.pdf", "rb") as f:
            files = {"file": ("test_paper.pdf", f, "application/pdf")}
            req = requests.post(f"{BASE_URL}/api/papers/upload", headers=headers, files=files)
            
            if req.status_code != 200:
                print(f"Failed to upload: {req.text}")
                sys.exit(1)
                
            paper_id = req.json()["id"]
            print(f"Uploaded successfully! Paper ID: {paper_id}")
    except FileNotFoundError:
        print("test_paper.pdf not found. Skipping file tests.")
        sys.exit(1)

    print(f"4. Expected Background task to run immediately for {paper_id}. Testing chat...")
    time.sleep(1) # wait for the background task to start loading FAISS
    
    # Actually, pdf_pipeline extracts and embeds 5-15 pages which takes 5-10 seconds
    print("Polling status...")
    for _ in range(15):
        req = requests.get(f"{BASE_URL}/api/papers/{paper_id}/status", headers=headers)
        status = req.json()["status"]
        if status == "ready":
             print("Paper is READY!")
             break
        print(f"Wait... status is {status}")
        time.sleep(3)
    
    req = requests.get(f"{BASE_URL}/api/papers/{paper_id}/status", headers=headers)
    if req.json()["status"] != "ready":
         print("Paper processing took too long or failed.")
         sys.exit(1)

    print("5. Testing /explain endpoint...")
    req = requests.post(f"{BASE_URL}/api/chat/explain", headers=headers, json={"paper_id": str(paper_id)})
    if req.status_code != 200:
        print(f"Explain failed: {req.text}")
    else:
        print("Explain successful! JSON:", req.json())

    print("END OF FLOW")

if __name__ == "__main__":
    test_flow()
