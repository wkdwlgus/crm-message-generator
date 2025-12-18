from supabase import create_client
from config import settings
from models.user import CustomerProfile
from typing import Optional

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_customer_from_db(user_id: str) -> Optional[CustomerProfile]:
    """Supabase customers 테이블에서 고객 데이터 조회"""
    result = supabase.from_("customers").select("*").eq("user_id", user_id).execute()
    if result.data:
        print(f"✅ 고객 데이터 조회 성공: {result.data[0]}")
        return CustomerProfile(**result.data[0])
    return None