"""
Message Generation API
GET /message 엔드포인트
"""
from fastapi import APIRouter, Header, HTTPException, Query
from models.message import MessageResponse, ErrorResponse
from services.supabase_client import supabase_client
from services.mock_data import get_mock_customer
from graph import message_workflow
from typing import Optional

router = APIRouter()


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
    channel: Optional[str] = Query("SMS", description="메시지 채널 (SMS, KAKAO, EMAIL)"),
):
    """
    개인화 메시지 생성 API
    
    Args:
        x_user_id: Header에서 추출한 고객 ID
        channel: 메시지 채널 (기본값: SMS)
        
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
            "strategy": {},
            "recommended_product_id": "",
            "product_data": {},
            "brand_tone": {},
            "message": "",
            "compliance_passed": False,
            "retry_count": 0,
            "error": "",
        }
        
        result = message_workflow.invoke(initial_state)
        
        # 3. 결과 검증
        if result.get("success", False):
            return result
        else:
            # 에러 응답
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "메시지 생성 중 알 수 없는 오류가 발생했습니다.")
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"메시지 생성 중 오류 발생: {str(e)}"
        )
