from supabase import create_client
from config import settings
from models.user import CustomerProfile
from typing import Optional, List, Dict, Any

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_customer_from_db(user_id: str) -> Optional[CustomerProfile]:
    """Supabase customers 테이블에서 고객 데이터 조회"""
    result = supabase.from_("customers").select("*").eq("user_id", user_id).execute()
    if result.data:
        print(f"✅ 고객 데이터 조회 성공: {result.data[0]}")
        return CustomerProfile(**result.data[0])
    return None

def get_customer_list(limit: int = 5) -> List[Dict[str, Any]]:
    """
    프론트엔드 페르소나 버튼 구성을 위해 고객 목록을 가져옵니다.
    필요한 필드만 선택해서 가져오면 더 빠릅니다.
    """
    try:
        # 필요한 컬럼만 쏙 골라서 가져오기
        result = supabase.table("customers").select(
            "user_id, name, membership_level, skin_type, keywords, preferred_tone, persona_id"
        ).order("user_id", desc=False).limit(limit).execute()
        
        return result.data or []
    except Exception as e:
        print(f"❌ 고객 목록 조회 실패: {str(e)}")
        return []