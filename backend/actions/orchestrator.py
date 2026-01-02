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
    intention: str  # 'GENERAL', 'EVENT', 'WEATHER'
    recommended_brand: List[str]  # 추천 브랜드 리스트 (최대 4개)
    strategy: int  # 1: Cold Start, 2: Behavioral, 3: Profile-based, 4: Hybrid
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


async def orchestrator_node(state: GraphState) -> GraphState:
    """
    Orchestrator Node
    
    고객 프로필을 분석하여 메시지 생성 전략을 수립합니다.
    """
    user_data = state["user_data"]
    channel = state.get("channel", "SMS")
    intention = state.get("intention", "GENERAL")
    
    # 1. 시나리오 결정 (Case 1-4)
    strategy_case = determine_strategy_case(user_data)
    
    # 2. 추천 브랜드 결정
    recommended_brand = determine_recommended_brand(user_data)
    
    # State 업데이트
    state["strategy"] = strategy_case
    state["recommended_brand"] = recommended_brand
    state["retry_count"] = 0
    state["success"] = False
    
    print(f"🎯 Orchestrator 결과:")
    print(f"  - Intention: {intention}")
    print(f"  - Strategy Case: {strategy_case} ({get_strategy_name(strategy_case)})")
    print(f"  - Recommended Brand: {recommended_brand}")
    
    return state


def get_strategy_name(case: int) -> str:
    """전략 케이스 이름 반환"""
    names = {
        1: "Cold Start (베스트셀러)",
        2: "Behavioral (행동 기반)",
        3: "Profile-based (프로필 기반)",
        4: "Hybrid (종합 분석)"
    }
    return names.get(case, "Unknown")


def determine_strategy_case(customer: CustomerProfile) -> int:
    """
    고객 데이터를 분석하여 추천 전략 케이스를 결정합니다.
    
    Case 1 (Cold Start): 데이터 전무 - 베스트셀러 추천
    Case 2 (Behavioral): 과거/실시간 데이터만 존재 - Item-to-Item CF
    Case 3 (Profile-based): 뷰티 프로필만 존재 - Content-based Filtering
    Case 4 (Hybrid): 모든 데이터 보유 - 재구매 + 프로필 + 행동 데이터
    
    Args:
        customer: 고객 프로필
        
    Returns:
        전략 케이스 번호 (1-4)
    """
    # 구매 이력 확인
    has_purchase_history = len(customer.purchase_history) > 0
    purchase_count = len(customer.purchase_history)
    
    # 실시간 행동 데이터 확인
    has_cart = len(customer.cart_items) > 0
    has_viewed = len(customer.recently_viewed_items) > 0
    has_behavioral_data = has_cart or has_viewed
    
    # 뷰티 프로필 확인
    has_beauty_profile = (
        len(customer.skin_type) > 0 and 
        len(customer.skin_concerns) > 0
    )
    
    # 케이스 결정 로직
    if not has_purchase_history and not has_behavioral_data:
        # Case 1: 아무 데이터도 없음 → Cold Start
        return 1
    
    elif not has_purchase_history and has_behavioral_data:
        # Case 2: 구매는 없지만 장바구니/최근 본 상품이 있음 → Behavioral
        return 2
    
    elif has_purchase_history and purchase_count <= 2 and has_beauty_profile:
        # Case 3: 구매 이력이 적고 뷰티 프로필이 명확함 → Profile-based
        return 3
    
    elif has_purchase_history and purchase_count >= 3:
        # Case 4: 구매 이력이 충분함 → Hybrid (재구매 + 프로필 + 행동)
        return 4
    
    else:
        # 기본값:1  (Cold Start)
        return 1


# 연령대별 브랜드 매핑
BRAND_AGE_MAPPING = {
    "이니스프리": ["10s", "20s"],
    "에스쁘아": ["20s", "30s"],
    "마몽드": ["20s", "30s"],
    "라네즈": ["20s", "30s"],
    "한율": ["30s", "40s"],
    "아이오페": ["30s", "40s", "50s"],
    "헤라": ["30s", "40s"],
    "프리메라": ["30s", "40s"],
    "에스트라": ["30s", "40s", "50s"],
    "설화수": ["40s", "50s", "60s+"]
}


def determine_recommended_brand(customer: CustomerProfile) -> List[str]:
    """
    고객 데이터를 기반으로 추천 브랜드 리스트를 결정합니다.
    
    로직:
    1. purchase_history에서 마지막 1-2개 브랜드
    2. cart_items에서 1-2개 브랜드
    3. 합쳐서 4개면 return, 아니면 연령대별 브랜드 추가
    
    Args:
        customer: 고객 프로필
        
    Returns:
        추천 브랜드 리스트 (최대 4개)
    """
    brands = set()
    
    # 1. 구매 이력에서 최근 1-2개 브랜드
    if len(customer.purchase_history) > 0:
        # 날짜 기준 내림차순 정렬 (최근 구매 우선)
        sorted_history = sorted(
            customer.purchase_history, 
            key=lambda x: x.purchase_date, 
            reverse=True
        )
        for item in sorted_history[:2]:
            brands.add(item.brand)
            if len(brands) >= 2:
                break
    
    # 2. 장바구니에서 1-2개 브랜드
    if len(customer.cart_items) > 0 and len(brands) < 4:
        for item in customer.cart_items[:2]:
            if item.brand:  # brand 필드가 있을 때만
                brands.add(item.brand)
                if len(brands) >= 4:
                    break
    
    # 3. 이미 4개면 반환
    if len(brands) >= 4:
        return list(brands)
    
    # 4. 부족하면 연령대별 브랜드 추가
    age_brands = get_brands_for_age(customer.age_group)
    for brand in age_brands:
        brands.add(brand)
        if len(brands) >= 4:
            break
    
    return list(brands)


def get_brands_for_age(age_group: str) -> List[str]:
    """
    연령대에 맞는 브랜드 리스트 반환
    
    Args:
        age_group: 연령대 (20s, 30s, 40s, 50s+)
        
    Returns:
        해당 연령대에 맞는 브랜드 리스트
    """
    # 50s+를 50s로 매핑
    normalized_age = age_group.replace("+", "")
    if normalized_age == "50s":
        # 50s+는 50s, 60s+ 모두 매칭
        matching_brands = [
            brand for brand, ages in BRAND_AGE_MAPPING.items()
            if "50s" in ages or "60s+" in ages
        ]
    else:
        matching_brands = [
            brand for brand, ages in BRAND_AGE_MAPPING.items()
            if age_group in ages
        ]
    
    return matching_brands if matching_brands else ["Laneige"]  # 기본값
