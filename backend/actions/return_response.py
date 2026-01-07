"""
Return Response Node
최종 응답 생성
"""
import json
import os
import random
from typing import TypedDict
from models.user import CustomerProfile
from models.message import GeneratedMessage, MessageResponse


class GraphState(TypedDict):
    """LangGraph State 정의"""
    user_id: str
    user_data: CustomerProfile
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
    retrieved_legal_rules: list  # 캐싱용: Compliance 노드에서 한 번 검색한 규칙 재사용


def _load_fallback_messages():
    """Fallback 메시지 JSON 파일 로드"""
    json_path = os.path.join(os.path.dirname(__file__), "..", "services", "fallback_messages.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_brand_fallback_message(brand_name: str, channel: str, customer_name: str) -> str:
    """
    브랜드별 Fallback 메시지 생성
    
    Args:
        brand_name: 브랜드 이름
        channel: 채널 (APPPUSH, KAKAO, EMAIL)
        customer_name: 고객 이름
        
    Returns:
        브랜드 톤앤매너가 반영된 Fallback 메시지
    """
    try:
        fallback_data = _load_fallback_messages()
        brand_messages = fallback_data.get("fallback_messages", {}).get(brand_name)
        
        if not brand_messages:
            # 브랜드가 없으면 기본 메시지
            return f"{customer_name}님, 특별한 혜택을 준비했습니다. 자세한 내용은 앱에서 확인해주세요."
        
        # 채널별 메시지가 있으면 사용, 없으면 safe_messages 중 랜덤 선택
        channel_variants = brand_messages.get("channel_variants", {})
        if channel in channel_variants:
            message_template = channel_variants[channel]
        else:
            safe_messages = brand_messages.get("safe_messages", [])
            if safe_messages:
                message_template = random.choice(safe_messages)
            else:
                message_template = "{customer_name}님, 특별한 혜택을 준비했습니다."
        
        # customer_name 치환
        return message_template.replace("{customer_name}", customer_name)
        
    except Exception as e:
        print(f"⚠️ Fallback 메시지 생성 실패: {e}")
        return f"{customer_name}님, 특별한 혜택을 준비했습니다. 자세한 내용은 앱에서 확인해주세요."


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
        # Compliance 실패 시 브랜드별 Fallback 응답
        print(f"❌ Compliance 실패: 브랜드별 Fallback Response 생성")
        
        # 고객 이름 추출
        customer_name = state['user_data'].name
        
        # 브랜드 이름 추출 (brand_tone에서)
        brand_name = state['brand_tone']
        
        # 채널 정보
        channel = state['channel']
        
        # 브랜드별 Fallback 메시지 생성
        fallback_message = _get_brand_fallback_message(brand_name, channel, customer_name)
        
        print(f"   브랜드: {brand_name}, 채널: {channel}, 고객: {customer_name}")
        print(f"   메시지: {fallback_message}")
        
        return {
            "success": True,
            "message": fallback_message
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
