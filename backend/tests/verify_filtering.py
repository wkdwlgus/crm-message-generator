import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to sys.path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Load .env explicitly
env_path = backend_path / ".env"
load_dotenv(dotenv_path=env_path)

from supabase import create_client
from models.user import CustomerProfile

def test_filtering_logic():
    print("🧪 Starting Filtering Logic Test...")
    
    # 1. Setup Mock User (Korean Profile)
    # Target: Persona 3, Warm Tone, Dry/Sensitive Skin
    target_p = "3"
    target_user = CustomerProfile(
        user_id="test_user",
        name="Test",
        age_group="30s",
        membership_level="VIP",
        
        # Korean Values
        skin_type=["수분부족지성", "복합성"], 
        skin_concerns=["모공", "트러블"],     
        preferred_tone="웜톤",
        keywords=[]
    )
    
    print(f"\n[Target User Setup]")
    print(f"- Persona: {target_p}")
    print(f"- Tone: {target_user.preferred_tone}")
    print(f"- Skin Types: {target_user.skin_type}")
    print(f"- Concerns: {target_user.skin_concerns}")
    
    # 2. DB Query (Simulating Orchestrator Logic)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    print(f"\n[Step 1] Executing DB Query...")
    # Logic: Persona Matches AND Tone Matches AND SkinType is in User's List
    query = supabase.table("user_data").select("*").eq("persona_id", target_p)
    
    # Filter 1: Tone (Exact)
    query = query.eq("preferred_tone", target_user.preferred_tone)
    
    # Filter 2: Skin Type (DB value must be in User's list)
    # The 'in_' filter checks if the column value is present in the provided list.
    if target_user.skin_type:
        query = query.in_("skin_type", target_user.skin_type)
        
    resp = query.execute()
    
    candidates = resp.data
    print(f"👉 DB Candidates Found: {len(candidates)}")
    
    if not candidates:
        print("❌ No candidates found in DB step. Test ends.")
        return

    # 3. Python Filter (Concerns & Keywords)
    print(f"\n[Step 2] Python Filtering (Concerns)...")
    
    final_matches = []
    user_concerns = set(target_user.skin_concerns)
    
    for row in candidates:
        # Parse Skin Concerns (String "A, B" -> Set {A, B})
        db_concerns_str = row.get("skin_concerns")
        db_concerns = set()
        if db_concerns_str:
            # Handle comma separated string
            parts = [c.strip() for c in db_concerns_str.split(",")]
            db_concerns = set(parts)
            
        # Logic: Check Overlap (At least one concern matches? Or Strict?)
        # Let's assume Overlap is enough for "Similar User"
        if not user_concerns:
            # If user has no concerns, skip concern filter? Or match users with no concerns?
            # Usually match all.
            is_match = True
        else:
            intersection = user_concerns.intersection(db_concerns)
            is_match = len(intersection) > 0 # At least one common concern
            
        if is_match:
            final_matches.append(row)
            
    print(f"👉 Final Matches after Concern Filter: {len(final_matches)}")
    
    if final_matches:
        print(f"\n[Sample Match Result]")
        sample = final_matches[0]
        print(f"- User ID: {sample.get('user_id')}")
        print(f"- Skin Type: {sample.get('skin_type')}")
        print(f"- Concerns: {sample.get('skin_concerns')}")
        print(f"- Purchases: {sample.get('brand_purchases')}")
        
        # Collect brands
        all_brands = []
        for u in final_matches:
            p_str = u.get("brand_purchases")
            if p_str:
                if isinstance(p_str, list):
                    all_brands.extend(p_str)
                else:
                    all_brands.extend([b.strip() for b in p_str.split(",")])
                    
        print(f"\n📦 Collected Top 5 Brands from {len(final_matches)} users:")
        from collections import Counter
        print(Counter(all_brands).most_common(5))

    else:
        print("❌ No matches after python filtering.")

if __name__ == "__main__":
    test_filtering_logic()
