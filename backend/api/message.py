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
    x_user_id: str = Header(..., description="고객 ID"),
    channel: Optional[str] = Query("APPPUSH", description="메시지 채널 (APPPUSH, SMS, KAKAO, EMAIL)"),
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
    # 1. 고객 데이터 조회 (Supabase -> Fallback to Mock)
    db_user = supabase_client.get_user(x_user_id)
    
    customer = None
    
    if db_user:
        # DB Dict -> CustomerProfile 변환
        try:
            from models.user import CustomerProfile, LastPurchase, ShoppingBehavior, CouponProfile, LastEngagement
            
            # Pydantic 모델 변환
            customer = CustomerProfile(
                user_id=db_user.get("user_id"),
                name=db_user.get("name"),
                age_group=db_user.get("age_group"),
                gender=db_user.get("gender"),
                membership_level=db_user.get("membership_level"),
                skin_type=db_user.get("skin_type", []),
                skin_concerns=db_user.get("skin_concerns", []),
                preferred_tone=db_user.get("preferred_tone"),
                keywords=db_user.get("keywords", []),
                acquisition_channel=db_user.get("acquisition_channel", "Unknown"),
                average_order_value=db_user.get("average_order_value", 0),
                average_repurchase_cycle_days=db_user.get("average_repurchase_cycle_days", 30),
                repurchase_cycle_alert=db_user.get("repurchase_cycle_alert", False),
                
                last_purchase=LastPurchase(**db_user["last_purchase"]) if db_user.get("last_purchase") else None,
                purchase_history=db_user.get("purchase_history", []),
                
                shopping_behavior=ShoppingBehavior(**db_user.get("shopping_behavior", {
                    "event_participation": "Low", 
                    "cart_abandonment_rate": "Rare", 
                    "price_sensitivity": "Medium"
                })),
                
                coupon_profile=CouponProfile(**db_user.get("coupon_profile", {
                    "history": [], 
                    "propensity": "Balanced", 
                    "preferred_type": "Percentage_Off"
                })),
                
                last_engagement=LastEngagement(**db_user.get("last_engagement", {})),
                cart_items=db_user.get("cart_items", []),
                recently_viewed_items=db_user.get("recently_viewed_items", [])
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
            
            # [추가] 프론트엔드 입력값
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

