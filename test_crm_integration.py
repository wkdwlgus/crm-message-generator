import time
import subprocess
import sys
import os
import httpx
import signal
import json
from pathlib import Path

def run_integration_test():
    # Paths
    root_dir = Path.cwd()
    backend_dir = root_dir / "backend"
    recsys_dir = root_dir / "RecSys"
    
    # 1. Start RecSys Server (Port 8001)
    print("🚀 Starting RecSys Server on port 8001...")
    recsys_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
        cwd=recsys_dir,
        stdout=subprocess.DEVNULL, # Suppress output to clean up log
        stderr=subprocess.PIPE
    )
    
    # 2. Start Backend Server (Port 8000)
    print("🚀 Starting Backend Server on port 8000...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    
    try:
        # Wait for servers to start
        print("⏳ Waiting 10 seconds for servers to initialize...")
        time.sleep(10)
        
        # 3. Make API Request
        url = "http://localhost:8000/message"
        params = {
            "reason": "weather",
            "weather_detail": "Rainy and humid",
            "brand": "이니스프리", 
            "persona": "P1"
        }
        headers = {"x-user-id": "user_0001"}
        
        print("\n📨 Sending Request to Backend...")
        try:
            response = httpx.get(url, params=params, headers=headers, timeout=60.0)
            print(f"✅ Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("\n🎉 Response Body:")
                print(response.json())
                with open("integration_result.txt", "w", encoding="utf-8") as f:
                    f.write(json.dumps(response.json(), indent=2, ensure_ascii=False))
            else:
                print("❌ Error Response:")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            print("--- Backend Stderr ---")
            print(backend_process.stderr.read().decode())
            print("--- RecSys Stderr ---")
            print(recsys_process.stderr.read().decode())

    finally:
        # 4. Cleanup
        print("\n🛑 Shutting down servers...")
        recsys_process.terminate()
        backend_process.terminate()
        recsys_process.wait()
        backend_process.wait()
        print("✅ Cleanup complete.")

if __name__ == "__main__":
    run_integration_test()
