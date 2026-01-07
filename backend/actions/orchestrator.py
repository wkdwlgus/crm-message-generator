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
    # [입력값] 프론트엔드/API에서 전달된 값
    crm_reason: str = ""       # CRM 발송 이유 (예: 날씨, 할인행사, 일반홍보)
    weather_detail: str = ""   # 날씨 상세 (crm_reason이 '날씨'일 때 사용. 예: 폭염 주의보, 장마철 습기)
    target_brand: str = ""     # 선택된 브랜드 (없으면 빈 문자열)
    target_persona: str = ""   # 선택된 페르소나 (예: Persona_1)
    recommended_brand: str  # 추천 브랜드 
    recommended_product_id: str
    product_data: dict
    brand_tone: dict
    channel: str
    message: str
    weather: str  # [NEW] 날씨 정보
    intent: str   # [NEW] 고객 의도 (구매/탐색/정보 등)
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
    channel = state["channel"]
    target_brand = state.get("target_brand", "")
    target_persona = state["target_persona"]
    
    crm_reason = state.get("crm_reason", "")
    
    # [로깅] 발송 의도 확인
    print(f"📋 CRM Reason: {crm_reason}")
    if crm_reason == "날씨":
        print(f"  - Detail: {state.get('weather_detail', 'N/A')}")

    # [Mock Data] 최근 이용 브랜드 랜덤 생성 (테스트용)
    # 실제 user_data 대신 랜덤하게 생성된 브랜드 리스트를 사용하고 싶다면 여기서 활용 가능
    # 현재 로직에서는 determine_recommended_brand 내부에서 랜덤 추출하므로 
    # 이 리스트는 로그 출력이나 추후 로직 확장에 사용
    if target_brand=="":
        mock_recent_brands = generate_mock_recent_brands(target_persona)
        # 페르소나 적합도 + 최근 이용 빈도(Mock Data) 기반 랭킹 산정
        recommended_brand = determine_recommended_brand(target_persona, mock_recent_brands)
    else:
        recommended_brand = [target_brand]
    
    # [NEW] 3. Mock Weather & Intent (추후 실제 데이터 연동 필요)
    import random
    mock_intent = random.choice(["regular", "events", "weather"])
    
    # Weather is only relevant if intent is 'weather'
    mock_weather = None
    if mock_intent == "weather":
        mock_weather = random.choice(["Sunny", "Cloudy", "Rainy", "Dry"])
    
    # State 업데이트
    state["recommended_brand"] = recommended_brand
    state["retry_count"] = 0
    state["weather"] = mock_weather
    state["intent"] = mock_intent
    
    print(f"🎯 Orchestrator 결과:")
    print(f"  - Recommended Brand: {recommended_brand}")
    # print(f"  - Persona: {persona.name} ({persona.persona_id})")
    
    return state


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
    - 페르소나 추천 브랜드: +3점 (Base Score)
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