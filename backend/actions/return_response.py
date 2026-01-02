"""
Return Response Node
최종 응답 생성
"""
from typing import TypedDict
from models.user import CustomerProfile
from models.message import GeneratedMessage, MessageResponse


class GraphState(TypedDict):
    """LangGraph State 정의"""
    user_id: str
    user_data: CustomerProfile
    intention: str
    strategy: int
    recommended_product_id: str
    product_data: dict
    brand_tone: dict
    channel: str
    message: str
    compliance_passed: bool
    retry_count: int
    error: str
    error_reason: str  # Compliance 실패 이유
    success: bool  # API 응답용

async def return_response_node(state: GraphState) -> dict:
    """
    Return Response Node
    
    최종 응답 데이터를 생성합니다.
    """
    compliance_passed = state.get("compliance_passed", False)
    
    if not compliance_passed:
        # Compliance 실패 시 에러 응답
        print(f"❌ Compliance 실패: {state.get('error_reason', '메시지 생성 실패')}")
        state["success"] = False
        return state
    
    # 성공 응답 생성
    print(f"✅ 최종 응답 생성: user={state['user_id']}, message={state['message'][:50]}...")
    state["success"] = True
    
    return state
