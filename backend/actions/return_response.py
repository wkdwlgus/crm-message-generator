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
from actions.orchestrator import GraphState  # [FIX] Import shared GraphState


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
    # [DEBUG] 진입 시점 상태 확인
    print("\n" + "="*80)
    print("📤 [Return Response Node] Started")
    print("="*80)
    print(f"🔍 cache_hit: {state.get('cache_hit', False)}")
    print(f"🔍 compliance_passed: {state.get('compliance_passed', False)}")
    current_message = state.get("message", "")
    print(f"🔍 state['message'] length: {len(current_message)} chars")
    print(f"🔍 state['message'] preview (first 150 chars):\n{current_message[:150]}")
    print("="*80 + "\n")
    
    # 고객 이름 추출 (이름이 없는 경우 '00' 사용)
    customer_name = getattr(state['user_data'], 'name', '00')
    
    if not state.get("compliance_passed", False):
        # Compliance 실패 시 브랜드별 Fallback 응답
        print(f"❌ Compliance 실패: 브랜드별 Fallback Response 생성")
        
        # 브랜드 이름 추출
        brand_name = state.get('target_brand')
        if not brand_name and isinstance(state.get('brand_tone'), dict):
            brand_name = state['brand_tone'].get('name', 'DefaultBrand')
        if not brand_name:
            brand_name = 'DefaultBrand'
        
        # 채널 정보
        channel = state.get('channel', 'SMS')
        
        # 브랜드별 Fallback 메시지 생성
        fallback_message = _get_brand_fallback_message(brand_name, channel, customer_name)
        
        print(f"   브랜드: {brand_name}, 채널: {channel}, 고객: {customer_name}")
        print(f"   메시지: {fallback_message}")
        
        return {
            "success": True,
            "message": fallback_message,
            "user_id": state["user_id"],
            "channel": channel
        }
    
    # 성공 응답 생성
    persona_used = state.get("target_persona", "default_persona")
    brand_name = state.get("target_brand")
    
    # [Moved Logic] Personalization Placeholder Replacement
    # Since personalize node is removed, we handle it here or ensure logic is self-contained
    # Perform placeholder substitution for customer name
    final_message = state.get("message", "")
    user_name = getattr(state['user_data'], 'name', '고객')
    
    if final_message:
         final_message = final_message.replace("{{customer_name}}", user_name) \
                           .replace("{customer_name}", user_name) \
                           .replace("{{Customer_Name}}", user_name) \
                           .replace("{Customer_Name}", user_name)

    generated_message = GeneratedMessage(
        user_id=state["user_id"],
        message_text=final_message,
        channel=state.get("channel", "SMS"),
        product_id=state.get("recommended_product_id"),
        brand_name=brand_name,
        persona_used=persona_used,
        compliance_passed=state.get("compliance_passed", True),
        retry_count=state.get("retry_count", 0),
    )
    print(f"✅ GeneratedMessage 생성: {generated_message.message_text}")
    response = MessageResponse(
        message=generated_message.message_text,
        user=generated_message.user_id,
        method=generated_message.channel,
    )

    print(f"✅ 최종 응답 생성 response: {response}")
    
    # [DEBUG] state 확인
    similar_ids = state.get("similar_user_ids", [])
    print(f"🔍 [DEBUG] similar_user_ids from state: {similar_ids}")
    print(f"🔍 [DEBUG] similar_user_ids length: {len(similar_ids)}")
    
    # API가 success: True를 확인할 수 있도록 추가
    result = response.model_dump()
    result["success"] = True
    result["similar_user_ids"] = similar_ids  # [NEW] 유사 유저 ID 포함
    
    print(f"🔍 [DEBUG] Final result keys: {result.keys()}")
    print(f"🔍 [DEBUG] Final result similar_user_ids: {result.get('similar_user_ids', 'NOT FOUND')}")
    
    return result
