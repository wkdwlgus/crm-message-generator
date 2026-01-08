"""
backend/api/message.py
[Hybrid Mode] 
- 상황 정보: 프론트엔드에서 수신
- 고객 정보: 백엔드가 Supabase DB에서 직접 조회 (Fixed Logic)
"""
from fastapi import APIRouter, Header, HTTPException, Query, Body
from models.message import MessageResponse, ErrorResponse, MessageRequest
from services.supabase_client import supabase_client
from services.user_service import get_customer_from_db, get_customer_list
from graph import message_workflow
from typing import Optional
import traceback

router = APIRouter()

@router.get(
    "/customers",
    summary="고객 목록 조회",
    description="프론트엔드 페르소나 선택 버튼(P1, P2...)을 위한 고객 리스트 반환"
)
async def get_customers_endpoint():
    """
    services/user_service.py의 함수를 호출하여 고객 목록을 반환
    """
    return get_customer_list()

@router.post(
    "/message",
    # response_model=MessageResponse,  # [FIX] 제거하여 dict 그대로 반환
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="개인화 메시지 생성",
    description="고객 ID를 기반으로 페르소나에 맞춘 개인화 CRM 메시지를 생성합니다.",
)
async def generate_message(
    request: MessageRequest
):
    """
    개인화 메시지 생성 API
    """
    # 0. Deduplication Check (중복 방지)
    # 특정 브랜드에 대해 최근 24시간 내에 발송된 메시지가 있는지 확인
    if request.targetBrand:
        recent_msgs = supabase_client.get_recent_messages(request.userId, days=1)
        for msg in recent_msgs:
            # 브랜드가 일치하고, (옵션) 성공한 메시지인 경우
            if msg.get('brand_name') == request.targetBrand:
                print(f"🚫 Duplicate message blocked for User {request.userId}, Brand {request.targetBrand}")
                # 프론트엔드에서 처리하기 쉽도록 429 Too Many Requests 또는 409 Conflict 반환
                # 여기서는 409 Conflict 사용
                raise HTTPException(
                    status_code=409, 
                    detail=f"최근 24시간 내에 '{request.targetBrand}' 브랜드에 대한 메시지가 이미 생성되었습니다."
                )

    # 1. 고객 데이터 조회 (Supabase -> Fallback to Mock)
    db_user = supabase_client.get_user(request.userId)  
    print(f"🧐 Fetching user data for ID: {request.userId}") 
    
    customer = None
    
    if db_user:
        # DB Dict -> CustomerProfile 변환
        try:
            from models.user import CustomerProfile
            
            # Pydantic 모델 변환
            # 사용자 요청에 따라 필수 4요소(피부타입, 고민, 톤, 키워드) 위주로 구성하고 나머지는 자동 처리
            customer = CustomerProfile(
                user_id=db_user.get("user_id"),
                name="00",  # 항상 '00'으로 고정
                age_group=db_user.get("age_group", "Unknown"),
                membership_level=db_user.get("membership_level", "General"),

                # [Core Elements] 사용자가 지정한 핵심 4요소
                skin_type=db_user.get("skin_type", []),
                skin_concerns=db_user.get("skin_concerns", []),
                preferred_tone=db_user.get("preferred_tone"),
                keywords=db_user.get("keywords", []),
                
                # 나머지 필드는 모델 정의에서 Optional이나 Default가 있으므로 생략 가능
            )
        except Exception as e:
            print(f"Error converting DB user data: {e}")
            customer = None

    # Fallback 없음: DB 실패 시 에러 처리
    if not customer:
        print(f"User '{request.userId}' not found in DB.")
        raise HTTPException(
            status_code=404,
            detail=f"고객 ID '{request.userId}'를 찾을 수 없습니다."
        )
        
    # 2. LangGraph 워크플로우 실행
    try:
        # [DEBUG] 프론트엔드에서 받은 요청 데이터 확인
        print(f"\n📥 [API Request Debug]")
        print(f"  - targetBrand: '{request.targetBrand}' (type: {type(request.targetBrand)})")
        print(f"  - hasBrand: {request.hasBrand}")
        print(f"  - persona: '{request.persona}'")
        print(f"  - intention: '{request.intention}'")
        
        initial_state = {
            "user_id": request.userId,
            "user_data": customer,
            "channel": request.channel or "SMS",
            
            # GraphState keys
            "crm_reason": request.intention or "신제품 출시 이벤트",
            "weather_detail": request.weatherDetail or "좋은 날씨",
            "target_brand": request.targetBrand or "",
            "target_persona": request.persona.replace("P", "") if request.persona and request.persona.startswith("P") else (request.persona or "1"),
            
            # Logic context
            "season": request.season or "계절 무관",
            "brand_name": request.targetBrand or "",
            "persona_name": request.persona or "1",
            
            # Output placeholders
            "message": "",
            "compliance_passed": False,
            "retry_count": 0,
            "error": "",
            "success": False,
            "retrieved_legal_rules": [],
            "product_data": {},  # Initialize to avoid KeyError in nodes
            "similar_user_ids": [],  # [FIX] 초기화 추가
        }

        print("🔥 AI 메시지 생성 시작...")
        
        result = await message_workflow.ainvoke(initial_state)
        
        # 3. 결과 검증
        if result.get("success", False):
            # [DEBUG] 최종 API 응답 확인
            similar_ids_final = result.get("similar_user_ids", [])
            print(f"🔍 [API DEBUG] Final result similar_user_ids: {len(similar_ids_final)} items")
            if similar_ids_final:
                print(f"   First 5: {similar_ids_final[:5]}")
            
            # [FIX] Dict를 직접 반환 (similar_user_ids 포함)
            # MessageResponse 모델 변환하지 않고 return_response_node의 결과를 그대로 반환
            api_response = {
                "message": result["message"],
                "user": result["user_id"],
                "method": result["channel"],
                "similar_user_ids": similar_ids_final
            }
            
            print(f"🔍 [API DEBUG] Returning API response with keys: {api_response.keys()}")
            
            return api_response
        else:
            # 에러 응답
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "메시지 생성 중 알 수 없는 오류가 발생했습니다.")
            )
    
    except Exception as e:
        print(f"❌ 로직 에러: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))