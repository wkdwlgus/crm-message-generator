
"""
Supabase Client Service
Supabase REST API와의 통신을 담당
"""
import httpx
from config import settings
from typing import Optional, Dict, Any, List

class SupabaseClient:
    def __init__(self):
        self.base_url = settings.SUPABASE_URL.rstrip("/")
        self.headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user profile from Supabase
        Table: customers (Assume table name)
        """
        try:
            url = f"{self.base_url}/rest/v1/customers" # Table Name Assumption
            params = {
                "user_id": f"eq.{user_id}",
                "select": "*"
            }
            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data[0] if data else None
        except Exception as e:
            print(f"Error fetching user from Supabase: {e}")
            return None

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch product details from Supabase
        Table: products (Assume table name)
        """
        try:
            url = f"{self.base_url}/rest/v1/products" # Table Name Assumption
            params = {
                "id": f"eq.{product_id}",
                "select": "*"
            }
            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data[0] if data else None
        except Exception as e:
            print(f"Error fetching product from Supabase: {e}")
            return None

# Global instance
supabase_client = SupabaseClient()
