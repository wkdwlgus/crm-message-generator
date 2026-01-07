
import os
import sys
from collections import Counter

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.supabase_client import supabase_client

def check_persona_distribution():
    print("🔍 Checking 'persona_category' distribution in 'customers' table...")
    
    try:
        # Fetch all customers (limit 100)
        resp = supabase_client.client.table("customers").select("user_id, persona_category").limit(100).execute()
        
        if not resp.data:
            print("⚠️ No customers found in DB.")
            return

        personas = [row.get("persona_category") for row in resp.data]
        distribution = Counter(personas)
        
        print("\n📊 Persona Category Distribution:")
        for p, count in distribution.items():
            print(f" - Value: '{p}' (Type: {type(p).__name__}): {count} users")
            
        print("\n📋 Sample Data (First 5):")
        for row in resp.data[:5]:
            print(f" - User: {row['user_id']}, Persona: {row.get('persona_category')}")
            
    except Exception as e:
        print(f"❌ Error querying DB: {e}")

if __name__ == "__main__":
    check_persona_distribution()
