
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
        Save generated message to 'generated_messages' table
        """
        try:
            response = self.client.table("generated_messages").insert(message_data).execute()
            if response.data:
                print("✅ Message saved to Supabase")
                return True
            else:
                print("❌ Failed to save message: No data returned")
                return False
        except Exception as e:
            print(f"Error saving message to Supabase: {e}")
            return False

    def get_recent_messages(self, user_id: str, product_id: str = None, days: int = 1) -> List[Dict[str, Any]]:
        """
        Check for recent messages for the same user (and optionally same product)
        """
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            query = self.client.table("generated_messages") \
                .select("*") \
                .eq("user_id", user_id) \
                .gt("generated_at", cutoff) \
                .order("generated_at", desc=True) \
                .limit(5)

            if product_id:
                query = query.eq("product_id", product_id)
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error checking recent messages: {e}")
            return []

# Global instance
supabase_client = SupabaseClient()
