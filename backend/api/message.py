"""
Message Generation API
GET /message 엔드포인트
"""
from fastapi import APIRouter, Header, HTTPException, Query
from models.message import MessageResponse, ErrorResponse
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
    channel: Optional[str] = Query("SMS", description="메시지 채널 (SMS, KAKAO, EMAIL, APP_PUSH)"),
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
    """
    # 1. 고객 데이터 조회
    # customer = get_mock_customer(x_user_id)
    customer = get_customer_from_db(x_user_id)
    
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
