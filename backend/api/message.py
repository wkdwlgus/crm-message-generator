"""
backend/api/message.py
[Hybrid Mode] 
- 상황 정보: 프론트엔드에서 수신
- 고객 정보: 백엔드가 Supabase DB에서 직접 조회 (Fixed Logic)
"""
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import traceback

# === 1. 모듈 로드 ===
try:
    from graph import message_workflow
    print("✅ Workflow loaded.")
except ImportError:
    message_workflow = None

try:
    from services.supabase_client import supabase_client
except ImportError:
    print("❌ Supabase Client 로드 실패")
    supabase_client = None

# === 2. 만능 고객 프로필 클래스 ===
class SafeCustomerProfile:
    def __init__(self, user_id, **kwargs):
        self.user_id = user_id
        # 기본값 "고객"으로 수정 (뒤에 '님'이 붙을 것 대비)
        self.name = kwargs.get("name", "고객") 
        self.age_group = kwargs.get("age_group", "알수없음")
        self.skin_type = kwargs.get("skin_type", ["복합성"])
        self.skin_concerns = kwargs.get("skin_concerns", [])
        self.keywords = kwargs.get("keywords", [])
        self.membership_level = kwargs.get("membership_level", "General")
        self.preferred_tone = kwargs.get("preferred_tone", "Polite")

# === 3. 요청 모델 ===
class MessageRequest(BaseModel):
    userId: str          # DB 조회용 Key
    channel: str
    intention: Optional[str] = "일반"
    hasBrand: bool = False
    targetBrand: Optional[str] = None
    season: Optional[str] = None
    weatherDetail: Optional[str] = None
    persona: Optional[str] = "P1" 

class MessageResponse(BaseModel):
    message: str
    user: str
    method: str

router = APIRouter()

@router.post("/message", response_model=MessageResponse)
async def generate_message_post(req: MessageRequest):
    print(f"\n🚀 [요청 도착] User ID: {req.userId} (DB 조회 시작)")
    
    if not message_workflow:
        raise HTTPException(status_code=500, detail="AI 워크플로우 로드 실패")

    # 1. DB에서 고객 정보 조회 (수파베이스)
    customer_data = {}
    try:
        if supabase_client:
            print(f"🔍 Supabase에서 ID {req.userId} 조회 시도...")
            
            # [수정된 부분] 
            # supabase_client 객체 자체를 사용하여 table 호출 시도
            # 만약 supabase_client가 래퍼라면 .client를 써야 할 수도 있음.
            # 가장 안전하게 hasattr로 체크
            
            client = supabase_client
            if hasattr(supabase_client, 'client'):
                client = supabase_client.client
            elif hasattr(supabase_client, 'supabase'):
                client = supabase_client.supabase
            
            # 테이블명: 'customers'가 맞는지 확인 필요 (users일 수도 있음)
            # 여기서는 customers로 시도
            response = client.table("customers") \
                .select("*") \
                .eq("user_id", req.userId) \
                .execute()
            
            if response.data and len(response.data) > 0:
                customer_data = response.data[0]
                print(f"✅ DB 조회 성공: {customer_data.get('name', '이름없음')}")
            else:
                print(f"⚠️ DB 조회 결과 없음 (ID: {req.userId}). 테이블명이나 ID를 확인하세요.")
        else:
            print("⚠️ Supabase 클라이언트가 로드되지 않았습니다.")
            
    except Exception as db_err:
        print(f"❌ DB 조회 에러 (무시하고 진행): {db_err}")
        # traceback.print_exc() # 상세 에러 보고 싶으면 주석 해제

    # 2. 프로필 객체 생성
    customer_obj = SafeCustomerProfile(
        user_id=req.userId,
        name=customer_data.get("name", "고객"), # DB 데이터 우선
        age_group=customer_data.get("age_group", "30대"),
        skin_type=customer_data.get("skin_type", ["복합성"]), 
        skin_concerns=customer_data.get("skin_concerns", ["수분 부족"]),
        keywords=customer_data.get("keywords", []),
        membership_level=customer_data.get("membership_level", "Family")
    )

    # 3. LangGraph 상태 구성
    try:
        target_brand = req.targetBrand if req.hasBrand else "DAPANDA"
        
        initial_state = {
            "user_id": req.userId,
            "user_data": customer_obj,
            "channel": req.channel,
            
            "customer_name": customer_obj.name,
            "skin_type": str(customer_obj.skin_type),
            "skin_concerns": str(customer_obj.skin_concerns),
            
            "intention": req.intention,
            "season": req.season or "계절 무관",
            "weather_detail": req.weatherDetail or "좋은 날씨",
            "brand_name": target_brand,
            
            # 기타 필수 필드
            "product_name": "추천 상품",
            "discounted_price": "0",
            "discount_rate": "0",
            "product_desc": "고객 맞춤 추천 제품",
            "review_keywords": "긍정 리뷰",
            "tone_style": "친절한",
            "tone_examples": "",
            "persona_name": req.persona,
            "message_goal": "소통",
            "communication_tone": "부드러움",
            "limit_text": "200자",
            "target_brand": target_brand,
            "target_persona": req.persona,
            "recommended_product_id": 101,
            "compliance_passed": False,
            "retry_count": 0,
            "error": "",
            "success": False
        }

        print("🔥 AI 메시지 생성 시작...")
        result = message_workflow.invoke(initial_state)
        
        final_msg = result.get("message", "")
        if not final_msg:
             final_msg = "메시지 생성 실패 (AI 응답 없음)"

        print(f"✅ 최종 응답 생성: {final_msg[:20]}...")

        return MessageResponse(
            message=final_msg,
            user=req.userId,
            method=req.channel
        )

    except Exception as e:
        print(f"❌ 로직 에러: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))