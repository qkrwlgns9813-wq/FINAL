from google import genai
import json

key1 = "AIzaSyBIgr9gcgknRjEMV-l8wTS4M2G-BIqZ2Bo"
client = genai.Client(api_key=key1)

print("--- All Models raw ---")
for m in client.models.list():
    # Print the model object as a dict if possible
    try:
        print(m.name)
    except:
        print(m)
