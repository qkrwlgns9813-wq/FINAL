import requests
import json

url = "http://localhost:5000/api/generate_ai_plan"
payload = {"period": "weekly"}
headers = {"Content-Type": "application/json"}

try:
    print("Sending request to AI endpoint...")
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    roadmap = data.get("yearly_roadmap", "")
    
    print("\n[Generated Roadmap Preview]")
    print(roadmap[:500] + "..." if len(roadmap) > 500 else roadmap)
    
    if "2026" in roadmap and "~" in roadmap:
        print("\n\nSUCCESS: Date range format found in roadmap!")
    else:
        print("\n\nWARNING: Date range format NOT found. Please check the output.")
        
except Exception as e:
    print(f"Error: {e}")
