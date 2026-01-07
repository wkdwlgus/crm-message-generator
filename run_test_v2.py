import time
import subprocess
import sys
import os
import httpx
from pathlib import Path

def run_integration_test():
    # Use absolute paths
    root_dir = Path(os.getcwd())
    backend_dir = root_dir / "backend"
    recsys_dir = root_dir / "RecSys"
    
    print(f"📂 Root: {root_dir}")
    
    # 1. Start RecSys (Port 8001)
    print("🚀 Starting RecSys Server...")
    recsys_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
        cwd=recsys_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    
    # 2. Start Backend (Port 8000)
    print("🚀 Starting Backend Server...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    
    try:
        print("⏳ Waiting 15 seconds for servers to initialize...")
        time.sleep(15)
        
        # 3. Test API
        url = "http://localhost:8000/message"
        params = {
            "reason": "weather",
            "weather_detail": "Rainy and humid",
            "brand": "이니스프리", 
            "persona": "P1"
        }
        headers = {"x-user-id": "user_0001"}
        
        print("\n📨 Sending Request...")
        print(f"URL: {url}")
        
        try:
            response = httpx.get(url, params=params, headers=headers, timeout=60.0)
            print(f"✅ Status Code: {response.status_code}")
            if response.status_code == 200:
                print("🎉 Success! Response:")
                print(response.json())
            else:
                print("❌ Failed Response:")
                print(response.text)
        except Exception as e:
            print(f"❌ HTTP Request failed: {e}")
            
    finally:
        print("\n🛑 Cleaning up servers...")
        recsys_process.terminate()
        backend_process.terminate()
        
        # Optional: Print Stderr for debugging
        if recsys_process.stderr:
            err = recsys_process.stderr.read().decode(errors='ignore')
            if err: print(f"RecSys Log:\n{err[:500]}...")
            
        if backend_process.stderr:
            err = backend_process.stderr.read().decode(errors='ignore')
            if err: print(f"Backend Log:\n{err[:500]}...")

if __name__ == "__main__":
    run_integration_test()
