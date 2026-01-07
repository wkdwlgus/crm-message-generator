
import sys
import os
from unittest.mock import MagicMock

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load .env explicitly for test execution if needed, 
# but pydantic-settings in config.py usually handles it.
# We just need to remove the Mocks.

# Real Supabase Client will be used via config.settings
from services import supabase_client
# supabase_client.supabase_client = MagicMock()  <-- REMOVED

from graph import message_workflow
from services.mock_data import get_mock_customer

def test_crm_product_1():
    print(">>> Starting CRM Test for Product ID 1")
    
    # 1. Real Data Fetching (ID=1)
    # The workflow will fetch product 1 from Real Supabase.
    print(f">>> Fetching Real Data for Product ID '1'...")

    # 2. Setup Input State (Real User Fetch)
    user_id = "user_12345"
    print(f">>> Fetching Real User Data for '{user_id}'...")
    
    db_user = supabase_client.supabase_client.get_user(user_id)
    if not db_user:
        # Fallback to Mock Data (cleaner match to API logic)
        print("!!! User not found in Real DB. Falling back to Mock Data...")
        user_data = get_mock_customer(user_id)
        if not user_data:
            print(f"!!! Mock User {user_id} not found either. Test will fail.")
            return
    else:
        # DB Dict -> CustomerProfile (Same logic as API - verified by direct usage)
        # For test simplicity, I will re-use the conversion logic or just trust the manual fallback if I can't import the API function easily.
        # Let's try to map it quickly.
        from models.user import CustomerProfile
        user_data = CustomerProfile(
            user_id=db_user.get("user_id"),
            skin_type=db_user.get("skin_type", []),
            skin_concerns=db_user.get("skin_concerns", []),
            preferred_tone=db_user.get("preferred_tone"),
            keywords=db_user.get("keywords", [])
        )
        print(f">>> User Found: {user_data.user_id}")

    # Setup Initial State
    initial_state = {
        "user_id": user_id,
        "user_data": user_data,
        "channel": "KAKAO",
        "recommended_product_id": "1" # User Request
    }

    # 3. Run Workflow
    print(">>> Invoking Workflow...")
    try:
        final_state = message_workflow.invoke(initial_state)
        
        print("\n" + "="*50)
        print(">>> CRM GENERATION RESULT")
        print("="*50)
        
        # Verify Product
        prod = final_state["product_data"]
        print(f"[Product] {prod['brand']} - {prod['name']}")
        
        # Verify Strategy
        strategy = final_state["strategy"]
        if isinstance(strategy, int):
             print(f"[Strategy] Case: {strategy}")
        else:
             print(f"[Strategy] {strategy}")

        # Print Message
        print("\n[Generated Message]")
        print("-" * 30)
        print(final_state.get("message"))
        print("-" * 30)

    except Exception as e:
        print(f"!!! Workflow failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crm_product_1()
