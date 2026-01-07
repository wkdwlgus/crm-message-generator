import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to sys.path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

# Load .env explicitly
env_path = backend_path / ".env"
load_dotenv(dotenv_path=env_path)

try:
    from supabase import create_client
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    supabase = create_client(url, key)
    
    print("\n--- Inspecting 'user_data' values ---")
    resp = supabase.table("user_data").select("skin_type, preferred_tone, skin_concerns").limit(5).execute()
    
    for i, row in enumerate(resp.data):
        print(f"[{i+1}] Skin Type: {row.get('skin_type')} (Type: {type(row.get('skin_type'))})")
        print(f"    Tone: {row.get('preferred_tone')} (Type: {type(row.get('preferred_tone'))})")
        concerns = row.get('skin_concerns')
        print(f"    Concerns: {concerns} (Type: {type(concerns)})")
        print(f"    Keywords: {row.get('keywords')} (Type: {type(row.get('keywords'))})")
        print("-" * 30)

except Exception as e:
    print(f"❌ Error: {e}")
