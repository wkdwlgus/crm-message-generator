import httpx
import asyncio
import sys

async def test_api():
    url = "http://localhost:8000/message"
    params = {
        "reason": "weather",
        "weather_detail": "Rainy and humid",
        "brand": "이니스프리",  # Optional, let's specify to be sure or leave empty
        "persona": "P1"
    }
    headers = {"x-user-id": "user_0001"}
    
    print(f"Testing API: {url}")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("Response JSON:")
                print(response.json())
            else:
                print("Error:", response.text)
    except httpx.ConnectError:
        print("Failed to connect to localhost:8000. Server might be down.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
