import httpx
import json
import sys

def test_api():
    url = "http://localhost:8000/message"
    params = {
        "reason": "weather",
        "weather_detail": "Rainy and humid",
        "brand": "이니스프리",
        "persona": "P1"
    }
    headers = {"x-user-id": "user_0001"}
    
    print(f"Testing API: {url}")
    print(f"Params: {params}")
    
    try:
        # Timeout increased just in case LLM is slow
        response = httpx.get(url, params=params, headers=headers, timeout=60.0)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API Success!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ API Failed: {response.text}")
            
    except httpx.ConnectError:
        print("❌ Connection Failed: Is localhost:8000 running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api()
