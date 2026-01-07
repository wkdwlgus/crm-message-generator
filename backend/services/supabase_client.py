
"""
Supabase Client Service
Supabase REST API와의 통신을 담당
"""
from supabase import create_client, Client
from config import settings
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user profile from Supabase
        Table: customers
        """
        try:
            response = self.client.table("customers").select("*").eq("user_id", user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error fetching user from Supabase: {e}")
            return None

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch product details from Supabase
        Table: products
        """
        try:
            response = self.client.table("products").select("*").eq("id", product_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error fetching product from Supabase: {e}")
            return None

    def save_generated_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Save generated message to 'crm_message_history' table
        """
        try:
            # Prepare payload matching crm_message_history schema
            # Schema: brand, persona, intent, weather, beauty_profile, message_content, channel, query_signature
            
            payload = {
                "brand": message_data.get("brand_name") or message_data.get("brand", "Unknown"),
                "persona": message_data.get("persona_used") or message_data.get("persona", "Unknown"),
                "intent": message_data.get("intent", "Marketing"),
                "weather": message_data.get("weather", None),
                "beauty_profile": message_data.get("beauty_profile", {}),
                "message_content": message_data.get("message_text") or message_data.get("message_content", ""),
                "channel": message_data.get("channel", None)
            }

            response = self.client.table("crm_message_history").insert(payload).execute()
            if response.data:
                print("✅ Message saved to Supabase (crm_message_history)")
                return True
            else:
                print("❌ Failed to save message: No data returned")
                return False
        except Exception as e:
            print(f"Error saving message to Supabase: {e}")
            return False

    def get_recent_messages(self, user_id: str, product_id: str = None, days: int = 1) -> List[Dict[str, Any]]:
        """
        Check for recent messages.
        Note: 'crm_message_history' does NOT record user_id, so we cannot filter by user history.
        Returning empty list to bypass.
        """
        return []

# Global instance
supabase_client = SupabaseClient()
