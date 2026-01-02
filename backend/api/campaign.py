"""
Campaign API
통합 캠페인 생성 엔드포인트 (/campaign)
"""
from fastapi import APIRouter, Header, HTTPException, Body
from models.message import MessageResponse, ErrorResponse
from services.mock_data import get_mock_customer
from graph import message_workflow
from typing import Optional

router = APIRouter()

@router.post(
    "/campaign",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="통합 캠페인 생성 (추천 + 메시지)",
    description="고객 정보와 의도(Intention)를 기반으로 상품 추천과 CRM 메시지를 한 번에 생성합니다.",
)
async def generate_campaign(
    x_user_id: str = Header(..., description="고객 ID"),
    intention: str = Body("GENERAL", description="캠페인 의도 (GENERAL, EVENT, WEATHER)"),
    channel: str = Body("SMS", description="메시지 채널 (SMS, KAKAO, EMAIL)"),
):
    """
    통합 캠페인 생성 API
    
    내부적으로 추천 엔진과 메시지 엔진이 체이닝되어 실행됩니다.
    """
    # 1. 고객 데이터 조회
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
            "intention": intention,
            "channel": channel,
            "strategy": 1,
            "recommended_brand": [],
            "recommended_product_id": "",
            "product_data": {},
            "brand_tone": {},
            "message": "",
            "compliance_passed": False,
            "retry_count": 0,
            "error": "",
            "error_reason": "",
            "success": False,
        }
        
        # 워크플로우 실행
        result = message_workflow.invoke(initial_state)
        
        # 3. 결과 반환
        if result.get("success", False):
            return MessageResponse(
                message=result["message"],
                user=result["user_id"],
                method=result["channel"]
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "캠페인 생성 중 오류가 발생했습니다.")
            )
            
    except Exception as e:
        print(f"❌ 캠페인 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
