"""
Orchestrator Node
고객 데이터를 분석하고 메시지 생성 전략 수립
"""
import json
import os
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import TypedDict, List, Set
from collections import Counter
from models.user import CustomerProfile
from models.persona import Persona


class GraphState(TypedDict):
    """LangGraph State 정의"""
    user_id: str
    user_data: CustomerProfile
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
    retrieved_legal_rules: list  # 캐싱용: Compliance 노드에서 한 번 검색한 규칙 재사용


def orchestrator_node(state: GraphState) -> GraphState:
    """
    Orchestrator Node
    
    고객 프로필을 분석하여 메시지 생성 전략을 수립합니다:
    - 시나리오 결정 (Case 0-3)
    - 추천 브랜드 결정
    - 페르소나 매칭
    
    Args:
        state: LangGraph State
        
    Returns:
        업데이트된 GraphState
    """
    user_data = state["user_data"]
    channel = state.get("channel", "SMS")
    
    # [Mock Data] 최근 이용 브랜드 랜덤 생성 (테스트용)
    # 실제 user_data 대신 랜덤하게 생성된 브랜드 리스트를 사용하고 싶다면 여기서 활용 가능
    # 현재 로직에서는 determine_recommended_brand 내부에서 랜덤 추출하므로 
    # 이 리스트는 로그 출력이나 추후 로직 확장에 사용
    strategy_case = 1
    mock_recent_brands = generate_mock_recent_brands(strategy_case)
    
    # 페르소나 적합도 + 최근 이용 빈도(Mock Data) 기반 랭킹 산정
    recommended_brand = determine_recommended_brand(strategy_case, mock_recent_brands)
    
    
    # State 업데이트
    state["strategy"] = strategy_case
    state["recommended_brand"] = recommended_brand
    state["retry_count"] = 0
    
    print(f"🎯 Orchestrator 결과:")
    print(f"  - Strategy Case: {strategy_case} ({get_strategy_name(strategy_case)})")
    print(f"  - Recommended Brand: {recommended_brand}")
    # print(f"  - Persona: {persona.name} ({persona.persona_id})")
    
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


def get_recent_brands(user_data: CustomerProfile, days: int = 30) -> Set[str]:
    """
    최근 N일 이내에 상호작용한(구매, 장바구니, 조회) 브랜드 목록을 추출합니다.
    """
    recent_brands = set()
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # 1. 구매 이력 확인
    for item in user_data.purchase_history:
        try:
            p_date = datetime.strptime(item.purchase_date, "%Y-%m-%d")
            if p_date >= cutoff_date:
                recent_brands.add(item.brand)
        except ValueError:
            continue
            
    # 2. 장바구니 확인
    for item in user_data.cart_items:
        try:
            # added_at이 있는 경우
            if hasattr(item, 'added_at'):
                a_date = datetime.strptime(item.added_at, "%Y-%m-%d")
                if a_date >= cutoff_date and item.brand:
                    recent_brands.add(item.brand)
        except ValueError:
            continue

    # 3. 최근 본 상품 (날짜 정보가 없으면 최근으로 간주하거나 제외)
    # 모델 정의상 날짜가 없으므로, 최근 본 상품은 모두 포함시킴 (또는 제외)
    # 여기서는 최근 본 상품도 관심 브랜드로 포함
    for item in user_data.recently_viewed_items:
        if item.brand:
            recent_brands.add(item.brand)
            
    return recent_brands


def generate_mock_recent_brands(personatype: int) -> List[str]:
    """
    사용자의 최근 이용 브랜드 리스트를 가중치 기반 랜덤으로 생성합니다.
    
    Args:
        personatype: 전략 케이스 번호 (1-5)
        
    Returns:
        랜덤하게 생성된 최근 이용 브랜드 리스트
    """
    try:
        # 현재 파일(orchestrator.py)과 같은 디렉토리에 있는 persona_db_v2.json 참조
        current_dir = Path(r"c:\Users\helen\Desktop\kt cloud tech up\advanced_project\blooming-v1\backend\actions")        
        json_path = current_dir / "persona_db.json"
        
        if not json_path.exists():
            return []
            
        with open(json_path, "r", encoding="utf-8") as f:
            persona_db = json.load(f)
            
        # 1. 전체 브랜드 리스트와 타겟 페르소나 브랜드 식별
        all_brands = set()
        target_brands = set()
        
        key = str(personatype)
        
        for p_id, p_data in persona_db.items():
            brands = p_data.get("recommended_brands", [])
            for b in brands:
                all_brands.add(b)
                if p_id == key:
                    target_brands.add(b)
        
        all_brands_list = list(all_brands)
        
        if not all_brands_list:
            return []
            
        # 2. 가중치 설정
        weights = []
        for brand in all_brands_list:
            if brand in target_brands:
                weights.append(10) # 타겟 브랜드 가중치
            else:
                weights.append(1)  # 그 외 브랜드 가중치
                
        # 3. 랜덤 개수 및 브랜드 추출
        # 1~10개 사이의 브랜드를 랜덤하게 선택
        count = random.randint(1, 10)
        recent_brands = random.choices(all_brands_list, weights=weights, k=count)
        
        # 중복 허용 (많이 추출된 브랜드 = 많이 이용한 브랜드)
        # recent_brands = list(dict.fromkeys(recent_brands))
        
        print(f"🎲 Mock Recent Brands (Persona {personatype}): {recent_brands}")
        return recent_brands

    except Exception as e:
        print(f"❌ Error generating mock recent brands: {e}")
        return []


def determine_recommended_brand(personatype: int, recent_brands: List[str]) -> List[str]:
    """
    페르소나 적합도와 최근 이용 빈도를 기반으로 브랜드 랭킹을 산정합니다.
    
    Scoring Logic:
    - 페르소나 추천 브랜드: +10점 (Base Score)
    - 최근 이용 브랜드: +1점 * 이용 횟수 (Frequency Score)
    
    Args:
        personatype: 전략 케이스 번호 (1-5)
        recent_brands: 최근 이용 브랜드 리스트 (중복 포함, 빈도 계산용)
        
    Returns:
        점수순으로 정렬된 추천 브랜드 리스트
    """
    try:
        # 현재 파일(orchestrator.py)과 같은 디렉토리에 있는 persona_db_v2.json 참조
        current_dir = Path(r"c:\Users\helen\Desktop\kt cloud tech up\advanced_project\blooming-v1\backend\actions")        
        json_path = current_dir / "persona_db.json"
        
        if not json_path.exists():
            print(f"⚠️ Warning: Persona DB file not found at {json_path}")
            return ["이니스프리"]
            
        with open(json_path, "r", encoding="utf-8") as f:
            persona_db = json.load(f)
            
        # 1. 타겟 페르소나 브랜드 식별
        target_brands = set()
        key = str(personatype)
        
        if key in persona_db:
            target_brands = set(persona_db[key].get("recommended_brands", []))
        else:
            print(f"⚠️ Warning: Persona type {personatype} not found in DB")
            
        # 2. 최근 이용 브랜드 빈도 계산
        recent_counts = Counter(recent_brands)
        
        # 3. 랭킹 후보군 선정 (페르소나 브랜드 + 최근 이용 브랜드)
        candidate_brands = target_brands.union(recent_counts.keys())
        
        if not candidate_brands:
            return ["이니스프리"]
            
        # 4. 점수 계산
        scored_brands = []
        for brand in candidate_brands:
            score = 0
            
            # 페르소나 적합도 점수
            if brand in target_brands:
                score += 3
                
            # 최근 이용 빈도 점수
            frequency = recent_counts.get(brand, 0)
            score += frequency * 1  # 1회당 1점 추가
            
            scored_brands.append((brand, score))
            
        # 5. 점수 내림차순 정렬
        scored_brands.sort(key=lambda x: x[1], reverse=True)
        
        # 6. 최고 점수 브랜드들 추출 (동점자 처리)
        if not scored_brands:
            return ["이니스프리"]
            
        max_score = scored_brands[0][1]
        top_brands = [brand for brand, score in scored_brands if score == max_score]
        
        print(f"📊 Brand Ranking (Persona {personatype}): {scored_brands}")
        print(f"🏆 Top Brands (Score {max_score}): {top_brands}")
        
        return top_brands

    except Exception as e:
        print(f"❌ Error determining recommended brand: {e}")
        return ["이니스프리"]