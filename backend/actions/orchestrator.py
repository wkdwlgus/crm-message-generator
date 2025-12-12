"""
Orchestrator Node
고객 데이터를 분석하고 메시지 생성 전략 수립
"""
from typing import TypedDict, List
from models.user import CustomerProfile
from models.persona import Persona


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


def orchestrator_node(state: GraphState) -> GraphState:
    """
    Orchestrator Node
    
    고객 프로필을 분석하여 메시지 생성 전략을 수립합니다:
    - 페르소나 매칭
    - 커뮤니케이션 톤 결정
    - 메시지 전략 수립
    
    Args:
        state: LangGraph State
        
    Returns:
        업데이트된 GraphState
    """
    user_data = state["user_data"]
    channel = state.get("channel", "SMS")
    
    # 1. 페르소나 매칭 로직
    persona = match_persona(user_data)
    
    # 2. 전략 수립
    strategy = {
        "persona_id": persona.persona_id,
        "persona_name": persona.name,
        "communication_tone": persona.communication_tone,
        "detail_level": persona.detail_level,
        "preferred_content_types": persona.preferred_content_types,
        "channel": channel,
        "personalization_variables": extract_personalization_variables(user_data),
        "message_goal": determine_message_goal(user_data),
    }
    
    state["strategy"] = strategy
    state["retry_count"] = 0
    
    return state


def match_persona(customer: CustomerProfile) -> Persona:
    """
    고객 데이터 기반 페르소나 매칭
    
    Args:
        customer: 고객 프로필
        
    Returns:
        매칭된 Persona
    """
    # 간단한 페르소나 매칭 로직 (실제로는 더 복잡한 규칙 필요)
    
    # VVIP 고객 → Premium Seeker
    if customer.membership_level in ["VVIP", "VIP"]:
        return Persona(
            persona_id="persona_premium",
            name="Premium Seeker",
            age_range="30-50",
            income_level="High",
            communication_tone="Sophisticated",
            detail_level="High",
            preferred_content_types=["Product_Story", "Ingredient_Details", "Expert_Recommendation"],
            interests=["Anti-aging", "Premium_Skincare", "Luxury_Beauty"],
            pain_points=["Lack_of_time", "Aging_concerns"]
        )
    
    # 20대 가성비 중시 → Savvy Shopper
    elif customer.age_group == "20s" and customer.shopping_behavior.price_sensitivity == "High":
        return Persona(
            persona_id="persona_savvy",
            name="Savvy Shopper",
            age_range="20-30",
            income_level="Medium",
            communication_tone="Friendly",
            detail_level="Medium",
            preferred_content_types=["Discount_Info", "Trending_Products", "Quick_Tips"],
            interests=["Trendy_Makeup", "Budget-friendly", "SNS_Popular"],
            pain_points=["High_prices", "Too_many_choices"]
        )
    
    # 기본 페르소나 → Balanced Buyer
    else:
        return Persona(
            persona_id="persona_balanced",
            name="Balanced Buyer",
            age_range="30-40",
            income_level="Medium",
            communication_tone="Warm",
            detail_level="Medium",
            preferred_content_types=["Product_Benefits", "Customer_Reviews", "Usage_Tips"],
            interests=["Quality_Products", "Skincare_Routine", "Self-care"],
            pain_points=["Information_overload", "Skin_concerns"]
        )


def extract_personalization_variables(customer: CustomerProfile) -> dict:
    """
    고객 데이터에서 개인화 변수 추출
    
    Args:
        customer: 고객 프로필
        
    Returns:
        개인화 변수 dict
    """
    variables = {
        "name": customer.name,
        "membership_level": customer.membership_level,
        "last_purchase_product": customer.last_purchase.product_name if customer.last_purchase else None,
        "skin_type": ", ".join(customer.skin_type),
        "skin_concerns": ", ".join(customer.skin_concerns),
        "repurchase_alert": customer.repurchase_cycle_alert,
    }
    
    return variables


def determine_message_goal(customer: CustomerProfile) -> str:
    """
    고객 상태 기반 메시지 목표 결정
    
    Args:
        customer: 고객 프로필
        
    Returns:
        메시지 목표 (예: "재구매 유도", "신상품 소개", "장바구니 유도")
    """
    # 재구매 주기 알림이 있으면 재구매 유도
    if customer.repurchase_cycle_alert:
        return "재구매 유도"
    
    # 장바구니에 상품이 있으면 장바구니 유도
    if customer.cart_items:
        return "장바구니 구매 유도"
    
    # 최근 방문했지만 구매 안 함 → 신상품 소개
    if customer.last_engagement:
        return "신상품 소개"
    
    # 기본: 제품 추천
    return "맞춤 제품 추천"
