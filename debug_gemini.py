import requests
import os
import json

API_KEY = "AIzaSyCWyaHwLI3zeUsKNJlSmiHt3dA4Nz88Hzw"

models_to_test = [
    "gemini-3-flash-preview",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-2.0-flash-exp",
    "gemini-pro"
]

prompt = "Hello. Reply with 'OK'."

print(f"🔬 DEBUGGING GEMINI API CONNECTION (Key: ...{API_KEY[-4:]})")
print("="*60)

for model in models_to_test:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    print(f"👉 Testing Model: {model}")
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS! Response: {response.json()['candidates'][0]['content']['parts'][0]['text']}")
            print(f"   🏆 WINNER: {model} works perfectly.")
        else:
            print(f"   ❌ FAILED. Response: {response.text[:150]}...")
            
    except Exception as e:
        print(f"   ⚠️ EXCEPTION: {e}")
    print("-" * 60)

input("\nPress Enter to exit...")
