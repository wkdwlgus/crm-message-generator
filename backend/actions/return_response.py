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
    strategy: dict
    recommended_product_id: str
    product_data: dict
    brand_tone: dict
    channel: str
    message: str
    compliance_passed: bool
    retry_count: int
    error: str


def return_response_node(state: GraphState) -> dict:
    """
    Return Response Node
    
    최종 응답 데이터를 생성합니다.
    
    Args:
        state: LangGraph State
        
    Returns:
        API 응답 딕셔너리
    """
    if not state.get("compliance_passed", False):
        # Compliance 실패 시 에러 응답
        return {
            "success": False,
            "error": state.get("error", "메시지 생성 실패"),
            "retry_count": state.get("retry_count", 0),
        }
    
    # 성공 응답 생성
    strategy_input = state["strategy"]
    persona_id = "default_persona"
    if isinstance(strategy_input, dict):
        persona_id = strategy_input.get("persona_id", "default_persona")
    
    generated_message = GeneratedMessage(
        user_id=state["user_id"],
        message_text=state["message"],
        channel=state.get("channel", "SMS"),
        product_id=state["recommended_product_id"],
        persona_id=persona_id,
        compliance_passed=state.get("compliance_passed", True),  # 🚨 추가 필수
        retry_count=state.get("retry_count", 0),
    )
    
    response = MessageResponse(
        message=generated_message.message_text,
        user=generated_message.user_id,
        method=generated_message.channel,
    )

    print(f"✅ 최종 응답 생성 response: {response}")
    
    return response.model_dump()
