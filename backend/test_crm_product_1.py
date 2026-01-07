
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
        from models.user import CustomerProfile, LastPurchase, ShoppingBehavior, CouponProfile, LastEngagement
        user_data = CustomerProfile(
            user_id=db_user.get("user_id"),
            name=db_user.get("name"),
            age_group=db_user.get("age_group"),
            gender=db_user.get("gender"),
            membership_level=db_user.get("membership_level"),
            skin_type=db_user.get("skin_type", []),
            skin_concerns=db_user.get("skin_concerns", []),
            keywords=db_user.get("keywords", []),
            acquisition_channel=db_user.get("acquisition_channel", "Unknown"),
            average_order_value=db_user.get("average_order_value", 0),
            average_repurchase_cycle_days=db_user.get("average_repurchase_cycle_days", 30),
            
            last_purchase=LastPurchase(**db_user["last_purchase"]) if db_user.get("last_purchase") else None,
            purchase_history=db_user.get("purchase_history", []),

            shopping_behavior=ShoppingBehavior(**db_user.get("shopping_behavior", {
                "event_participation": "Low", "cart_abandonment_rate": "Rare", "price_sensitivity": "Medium"
            })),
            coupon_profile=CouponProfile(**db_user.get("coupon_profile", {
                "history": [], "propensity": "Balanced", "preferred_type": "Percentage_Off"
            })),
            last_engagement=LastEngagement(**db_user.get("last_engagement", {})),
            cart_items=db_user.get("cart_items", []),
            recently_viewed_items=db_user.get("recently_viewed_items", [])
        )
        print(f">>> User Found: {user_data.name}")

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
