"""
Message Generation API
GET /message 엔드포인트
"""
from fastapi import APIRouter, Header, HTTPException, Query
from models.message import MessageResponse, ErrorResponse
from services.supabase_client import supabase_client
from services.mock_data import get_mock_customer
from services.user_service import get_customer_from_db, get_customer_list
from graph import message_workflow
from typing import Optional

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

@router.get(
    "/message",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="개인화 메시지 생성",
    description="고객 ID를 기반으로 페르소나에 맞춘 개인화 CRM 메시지를 생성합니다.",
)
async def generate_message(
    x_user_id: str = Header("user_0001", description="고객 ID"),
    channel: Optional[str] = Query("SMS", description="메시지 채널 (APPPUSH, SMS, KAKAO, EMAIL)"),
    reason: Optional[str] = Query("신제품 출시 이벤트", description="CRM 발송 이유 (날씨, 할인행사, 일반홍보)"),
    weather_detail: Optional[str] = Query(None, description="날씨 상세 정보 (예: 폭염 주의보, 건조한 가을) - reason='날씨'일 때 필수"),
    brand: Optional[str] = Query("이니스프리", description="선택된 브랜드 (없을 경우 자동 추천)"),
    persona: Optional[str] = Query("P1", description="선택된 페르소나 (예: P1, P2)")
):
    """
    개인화 메시지 생성 API
    
    Args:
        x_user_id: Header에서 추출한 고객 ID (기본값: U001 - 테스트용)
        channel: 메시지 채널 (기본값: SMS)
        reason: CRM 발송 목적 (기본값: 신제품 출시 이벤트)
        brand: 특정 브랜드 지정 시 (기본값: 이니스프리)
        persona: 특정 페르소나 지정 시 (기본값: P1)
        
    Returns:
        MessageResponse: 생성된 메시지 응답
        
    Raises:
        HTTPException: 고객 정보를 찾을 수 없거나 메시지 생성 실패 시
    """
    # 0. Deduplication Check (중복 방지)
    # 특정 브랜드에 대해 최근 24시간 내에 발송된 메시지가 있는지 확인
    if brand:
        recent_msgs = supabase_client.get_recent_messages(x_user_id, days=1)
        for msg in recent_msgs:
            # 브랜드가 일치하고, (옵션) 성공한 메시지인 경우
            if msg.get('brand_name') == brand:
                print(f"🚫 Duplicate message blocked for User {x_user_id}, Brand {brand}")
                # 프론트엔드에서 처리하기 쉽도록 429 Too Many Requests 또는 409 Conflict 반환
                # 여기서는 409 Conflict 사용
                raise HTTPException(
                    status_code=409, 
                    detail=f"최근 24시간 내에 '{brand}' 브랜드에 대한 메시지가 이미 생성되었습니다."
                )

    # 1. 고객 데이터 조회 (Supabase -> Fallback to Mock)
    db_user = supabase_client.get_user(x_user_id)
    
    customer = None
    
    if db_user:
        # DB Dict -> CustomerProfile 변환
        try:
            from models.user import CustomerProfile
            
            # Pydantic 모델 변환
            # 사용자 요청에 따라 필수 4요소(피부타입, 고민, 톤, 키워드) 위주로 구성하고 나머지는 자동 처리
            customer = CustomerProfile(
                user_id=db_user.get("user_id"),

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

    # Fallback to Mock Data if DB failed or empty
    if not customer:
        print(f"User '{x_user_id}' not found in DB. Trying Mock Data...")
        customer = get_mock_customer(x_user_id)
    
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"고객 ID '{x_user_id}'를 찾을 수 없습니다."
        )
        
    # 2. LangGraph 워크플로우 실행
    try:
        initial_state = {
            "user_id": x_user_id,
            "user_data": customer,
            "channel": channel,
            "crm_reason": reason or "",
            "weather_detail": weather_detail or "",  # 추가됨
            "target_brand": brand or "",
            "target_persona": persona or "",
            "recommended_product_id": "",
            "product_data": {},
            "brand_tone": {},
            "message": "",
            "compliance_passed": False,
            "retry_count": 0,
            "error": "",
            "error_reason": "",  # Compliance 실패 이유
            "success": False,  # 초기값
        }
        
        result = message_workflow.invoke(initial_state)
        
        # 3. 결과 검증
        if result.get("success", False):
            # [Added] Save to Supabase (비동기 처리 권장되나 여기선 동기 처리)
            try:
                save_data = {
                    "user_id": result["user_id"],
                    "message_text": result["message"],
                    "channel": result["channel"],
                    "persona_used": result.get("target_persona"),
                    "product_id": result.get("recommended_product_id"),
                    "brand_name": result.get("target_brand") or result.get("recommended_brand"),
                    "compliance_passed": result.get("compliance_passed", False),
                    "retry_count": result.get("retry_count", 0)
                }
                supabase_client.save_generated_message(save_data)
            except Exception as e:
                print(f"⚠️ Failed to save generated message: {e}")

            # MessageResponse 모델로 변환하여 반환
            return MessageResponse(
                message=result["message"],
                user=result["user_id"],
                method=result["channel"]
            )
        else:
            # 에러 응답
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "메시지 생성 중 알 수 없는 오류가 발생했습니다.")
            )
    
    except Exception as e:
        print(f"❌ 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"메시지 생성 중 오류 발생: {str(e)}"
        )

