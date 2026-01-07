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


from services.supabase_client import supabase_client

# [Translation Maps] DB(Eng) -> User(Kor)
# 1. Skin Type
SKIN_TYPE_MAP = {
    "Combination": "복합성",
    "Dry": "건성",
    "Oily": "지성",
    "Dehydrated_Oily": "수분부족지성"
}

# 2. Skin Concerns
CONCERN_MAP = {
    "Sensitive": "민감성",
    "Acne": "트러블",
    "Lack_of_Elasticity": "탄력없음",
    "Wrinkle": "주름",
    "Dullness": "칙칙함",
    "Pores": "모공",
    "None": "고민없음"
}

# 3. Preferred Tone
TONE_MAP = {
    "Cool": "쿨톤",
    "Warm": "웜톤"
}

# 4. Keywords
KEYWORD_MAP_SIMPLIFIED = {
    "Vegan": "비건",
    "Clean_Beauty": "클린 뷰티",
    "Hypoallergenic": "저자극",
    "Dermatologist_Tested": "피부과 테스트 완료",
    "Non_Comedogenic": "논코메도제닉",
    "Fragrance_Free": "무향",
    "Anti_Aging": "안티에이징",
    "Firming": "탄력 케어",
    "Moisture": "보습",
    "Glow": "윤광",
    "Premium": "프리미엄",
    "Limited": "한정판",
    "New_Arrival": "신상",
    "Gift": "선물용",
    "Sale": "할인",
    "whitening": "미백",
    "Nutrition": "영양공급",
    "Big_Size": "대용량",
    "One_plus_One": "1+1",
    "free_gift": "사은품",
    "Cica": "시카",
    "PDRN": "피디알엔",
    "Rethinol": "레티놀",
    "Collab": "콜라보",
    "Packaging": "패키징",
    "Glitter": "글리터",
    "Set_Item": "세트상품",
    "Luxury": "럭셔리",
    "Gift_Packaging": "선물포장"
}

class GraphState(TypedDict):
    """LangGraph State 정의"""
    user_id: str
    user_data: CustomerProfile
    # [입력값] 프론트엔드/API에서 전달된 값
    crm_reason: str = ""       # CRM 발송 이유 (예: 날씨, 할인행사, 일반홍보)
    weather_detail: str = ""   # 날씨 상세 (crm_reason이 '날씨'일 때 사용. 예: 폭염 주의보, 장마철 습기)
    target_brand: str = ""     # 선택된 브랜드 (없으면 빈 문자열)
    target_persona: str = ""   # 선택된 페르소나 (예: Persona_1)
    use_crm_cache: bool = True # [NEW] CRM 메시지 재사용 여부 (Default: True)
    recommended_brand: str  # 추천 브랜드 
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
    channel = state["channel"]
    target_brand = state.get("target_brand", "")
    target_persona = state["target_persona"]
    
    # [Fix] Clean P prefix if exists (Handle both 'P1' and '1')
    print(f"🧐 Orchestrator Input - Target Persona: {target_persona}")
    
    crm_reason = state.get("crm_reason", "")
    
    # [로깅] 발송 의도 확인
    print(f"📋 CRM Reason: {crm_reason}")
    if crm_reason == "날씨":
        print(f"  - Detail: {state.get('weather_detail', 'N/A')}")

    # [Mock Data] 최근 이용 브랜드 랜덤 생성 (테스트용) -> 제거 또는 필요 시 다른 로직으로 대체
    # 여기서는 Mock 로직을 제거하고 단순히 target_brand가 없으면 기본 로직(빈 리스트 등)을 타게 수정하거나
    # determine_recommended_brand 내부에서도 Mock 사용을 제거해야 함.
    # 일단 요구사항에 따라 mock removal.
    print("target_brand:", target_brand)
    
    if target_brand=="":
        print("⚠️ Target Brand is empty, using DB-based recommendation logic.")
        # [DB Query] Mock 대신 실제 DB 데이터 사용 (user_data 필터링 추가)
        recent_brands = get_persona_recent_brands(target_persona, user_data)
        recommended_brand = determine_recommended_brand(target_persona, recent_brands)
    else:
        recommended_brand = [target_brand]
    
    # State 업데이트
    state["recommended_brand"] = recommended_brand
    state["retry_count"] = 0
    
    print(f"🎯 Orchestrator 결과:")
    print(f"  - Recommended Brand: {recommended_brand}")
    # print(f"  - Persona: {persona.name} ({persona.persona_id})")
    
    return state



def get_persona_recent_brands(personatype: str, target_user: CustomerProfile) -> List[str]:
    """
    Supabase 'customers' 테이블에서 
    1) 해당 페르소나(persona_id)를 가지고
    2) Target User와 [피부타입, 고민, 톤, 키워드]가 일치하는 유사 사용자들의
    'brand_purchases' 데이터를 조회하여 통합 반환합니다.
    """
    try:
        # P 접두사 제거
        target_p = str(personatype)
        print(f"🔎 [DB] Fetching similar users for persona: {target_p}")
        
        # [Optimization] Apply Filters on DB Side to bypass 1000 limit issue.
        # Reverse Map (Kor -> Eng)
        # Note: Maps are many-to-one sometimes, but here we assume simple inversion works for main keys.
        
        query = supabase_client.client.table("user_data").select("*").eq("persona_id", target_p)

        # 1. Preferred Tone Filter
        # User input is Korean (e.g., "웜톤"). Find English key.
        target_tone_eng = None
        for k, v in TONE_MAP.items():
            if v == target_user.preferred_tone:
                target_tone_eng = k
                break
        
        if target_tone_eng:
             query = query.eq("preferred_tone", target_tone_eng)
             
        # 2. Skin Type Filter (Subset Containment)
        # We want users who have AT LEAST the target types. (Or Exact equality?)
        # For now, let's use 'contains' which is safer for finding candidates.
        # User: ["건성"] -> DB must have "Dry"
        target_skin_eng = []
        for ut in target_user.skin_type:
            for k, v in SKIN_TYPE_MAP.items():
                if v == ut:
                    target_skin_eng.append(k)
                    break
        
        if target_skin_eng:
            # Postgres JSONB contains: column @> value
            query = query.contains("skin_type", target_skin_eng)

        # Execute
        resp = query.execute()
            
        # [Removed Fallback] User confirmed DB strictly uses numeric persona (e.g., '1', '2', '3')
        # Sending 'P3' caused invalid input syntax error for numeric/json columns.
        
        if not resp.data:
            print(f"⚠️ No users found for persona '{target_p}'.")
            return []
            
        # Python-side Filtering (Strict Matching with Translation)
        similar_users_brands = []
        
        # Target User Data (Assuming Korean)
        user_skin_type = set(target_user.skin_type)
        user_skin_concerns = set(target_user.skin_concerns)
        user_tone = target_user.preferred_tone
        user_keywords = set(target_user.keywords)
        
        match_count = 0
        
        for row in resp.data:
            # Skip self
            if row.get("user_id") == target_user.user_id:
                continue
                
            # 1. Skin Type Match (Translate DB Eng -> Kor)
            db_skin_types = row.get("skin_type", [])
            row_skin_type_kor = set()
            for t in db_skin_types:
                # Map or keep original if not found
                row_skin_type_kor.add(SKIN_TYPE_MAP.get(t, t))
                
            if row_skin_type_kor != user_skin_type:
                continue
                
            # 2. Skin Concerns Match
            db_concerns = row.get("skin_concerns", [])
            row_concerns_kor = set()
            for c in db_concerns:
                row_concerns_kor.add(CONCERN_MAP.get(c, c))
                
            if row_concerns_kor != user_skin_concerns:
                continue
                
            # 3. Tone Match
            db_tone = row.get("preferred_tone")
            row_tone_kor = TONE_MAP.get(db_tone, db_tone)
            if row_tone_kor != user_tone:
                # Try raw comparison just in case
                if db_tone != user_tone:
                    continue
                
            # 4. Keywords Match (Partial Overlap allowed or strict?)
            # Since full translation map is missing, let's try direct comparison 
            db_keywords = set(row.get("keywords", []))
            # If raw match works
            if db_keywords == user_keywords:
                pass # Match
            else:
                # Try simple mapping
                db_keywords_kor = set()
                for k in db_keywords:
                    # Try simplified map (map keys are MixedCase as provided by user)
                    if k in KEYWORD_MAP_SIMPLIFIED:
                        db_keywords_kor.add(KEYWORD_MAP_SIMPLIFIED[k])
                    elif k.lower() in KEYWORD_MAP_SIMPLIFIED: # Fallback to lowercase check
                        db_keywords_kor.add(KEYWORD_MAP_SIMPLIFIED[k.lower()]) 
                    else:
                        db_keywords_kor.add(k) # Keep original if no map
                
                if db_keywords_kor != user_keywords:
                    # [Debug Log] Unmatched Keywords
                    # print(f"  - Keyword Mismatch: DB({db_keywords_kor}) != User({user_keywords})")
                    continue
            
            # Matched!
            match_count += 1
            purchases = row.get("brand_purchases", [])
            if isinstance(purchases, list):
                similar_users_brands.extend(purchases)
            elif isinstance(purchases, str):
                 similar_users_brands.extend([b.strip() for b in purchases.split(",") if b.strip()])
                 
        print(f"👥 Found {match_count} similar users (Same Profile).")
        
        all_brands = [b for b in similar_users_brands if b]

        print(f"📦 Loaded Brands from Similar Users (Count: {len(all_brands)}): {all_brands[:10]}...")
        return all_brands

    except Exception as e:
        print(f"❌ Error fetching brands from DB: {e}")
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
        # [Debugging Log]
        print(f"🕵️ Determine Brand Input - Persona: {personatype}, Recent Brands: {recent_brands}")

        # 현재 파일(orchestrator.py)이 있는 위치 기준 (Relative Path)
        current_dir = Path(__file__).parent
        json_path = current_dir / "persona_db.json"
        
        if not json_path.exists():
            print(f"⚠️ Warning: Persona DB file not found at {json_path}")
            return ["이니스프리"]
            
        with open(json_path, "r", encoding="utf-8") as f:
            persona_db = json.load(f)
            
        # 1. 타겟 페르소나 브랜드 식별
        target_brands = set()
        key = str(personatype)
        if key.lower().startswith('p'):
            key = key[1:]
        
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