"""
Info Retrieval Node
필요한 정보 수집 (상품 추천, 브랜드 톤앤매너)
"""
from typing import TypedDict
from services.mock_data import get_mock_product, recommend_product_for_customer
from models.user import CustomerProfile
import httpx
from config import settings


class GraphState(TypedDict):
    """LangGraph State 정의"""
    user_id: str
    user_data: CustomerProfile
    recommended_brand: str  # orchestrator에서 결정된 추천 브랜드
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


def info_retrieval_node(state: GraphState) -> GraphState:
    """
    Info Retrieval Node
    
    메시지 생성에 필요한 정보를 수집합니다:
    - 추천 상품 정보 (RecSys API 호출)
    - 브랜드 톤앤매너
    
    Args:
        state: LangGraph State
        
    Returns:
        업데이트된 GraphState
    """
    user_data = state["user_data"]
    recommended_product_id = state.get("recommended_product_id") # Input으로 들어올 수도 있음
    product_data_input = state.get("product_data")
    
    recommended_product = None
    
    # 0. 이미 Product Data가 있는지 확인
    if product_data_input and product_data_input.get("product_id"):
        # 이미 데이터가 있으면 Fetch 생략
        brand_name = product_data_input.get("brand", "Unknown")
        # ID 동기화
        if not recommended_product_id:
            state["recommended_product_id"] = product_data_input.get("product_id")
    else:
        # 1. 상품 식별 (Input ID 우선, 없으면 추천 로직)
        if recommended_product_id:
            # Input으로 ID가 주어졌다면 해당 상품 조회
            from services.supabase_client import supabase_client
            product_data_raw = supabase_client.get_product(recommended_product_id)
            
            if product_data_raw:
                # DB에서 조회 성공 -> Mock Product 객체로 변환 (또는 Dict 직접 사용)
                # 여기서는 편의상 Mock 구조를 따르도록 Dict 변환
                recommended_product = convert_db_to_product_model(product_data_raw)
            else:
                # DB 조회 실패 시 Mock Fallback
                recommended_product = get_mock_product(recommended_product_id)
                if not recommended_product:
                    # Mock도 없으면 기본 추천 로직 수행
                    recommended_product = recommend_product_for_customer(user_data)
        else:
            # ID가 없으면 추천 로직 수행
            recommended_product = recommend_product_for_customer(user_data)
        
        # 새로 조회된 경우 Brand Name 추출
        brand_name = recommended_product.brand
    
    # 2. 브랜드 톤앤매너 조회 (CRM Guideline JSON 연동)
    brand_tone_data = get_brand_tone_from_guideline(brand_name)
    
    # 3. State 업데이트 (새로 조회된 경우에만)
    if recommended_product:
        state["recommended_product_id"] = recommended_product.product_id
        state["product_data"] = {
            "product_id": recommended_product.product_id,
            "brand": recommended_product.brand,
            "name": recommended_product.name,
            "category": {
                "major": recommended_product.category.major,
                "middle": recommended_product.category.middle,
                "small": recommended_product.category.small,
            },
            "price": {
                "original_price": recommended_product.price.original_price,
                "discounted_price": recommended_product.price.discounted_price,
                "discount_rate": recommended_product.price.discount_rate,
            },
            "review": {
                "score": recommended_product.review.score,
                "count": recommended_product.review.count,
                "top_keywords": recommended_product.review.top_keywords,
            },
            "description_short": recommended_product.description_short,
        }
    
    if brand_tone_data:
        state["brand_tone"] = brand_tone_data
    else:
        # 브랜드 정보가 없으면 기본값 설정
        state["brand_tone"] = {
            "brand_name": brand_name,
            "tone_manner_style": "Friendly",
            "tone_manner_examples": [],
        }

    return state


def get_brand_tone_from_guideline(brand_name_en: str) -> dict:
    """CRM Guideline JSON에서 브랜드 톤앤매너 조회"""
    import json
    import os
    
    # 1. JSON 로드
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_path, "services", "crm_guideline.json")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            guidelines = json.load(f)
    except Exception as e:
        print(f"Error loading crm_guideline.json: {e}")
        return None

    # 2. 브랜드명 매핑 (Eng -> Kor)
    # 실제 환경에서는 별도 매핑 테이블 관리 권장
    brand_mapping = {
        "Sulwhasoo": "설화수",
        "Hera": "헤라",
        "Laneige": "라네즈",
        "Mamonde": "마몽드",
        "IOPE": "아이오페",
        "Hannul": "한율", 
        "Hanyul": "한율",
        "Espoir": "에스쁘아",
        "Etude": "에뛰드",
        "Innisfree": "이니스프리",
        "Aestura": "에스트라",
        "Primera": "프리메라"
    }
    
    brand_name_kor = brand_mapping.get(brand_name_en, brand_name_en) # 매핑 없으면 그대로 사용 (혹시 한글일 수도 있음)
    
    # 3. 데이터 추출
    brands_data = guidelines.get("brands", {})
    target_brand = brands_data.get(brand_name_kor)
    
    if target_brand:
        return {
            "brand_name": brand_name_kor,
            "tone_manner_style": target_brand.get("tone_manner_style", "Professional"), # 기본값
            "tone_manner_examples": target_brand.get("tone_manner_examples", [])
        }
    
    return None


def convert_db_to_product_model(db_data: dict):
    """DB 데이터를 Product 모델 객체로 변환 (Schema Based)"""
    from models.product import Product, ProductCategory, ProductPrice, ProductReview, ProductAnalytics
    
    # Keywords Parsing (Text -> List)
    keywords_raw = db_data.get("keywords", "")
    keywords_list = [k.strip() for k in keywords_raw.split(",")] if keywords_raw else []
    
    return Product(
        product_id=str(db_data.get("id", "")),
        brand=db_data.get("brand", "Unknown"),
        name=db_data.get("name", "Unknown Product"),
        category=ProductCategory(
            major=db_data.get("category_major") or "",
            middle=db_data.get("category_middle") or "",
            small=db_data.get("category_small") or ""
        ),
        price=ProductPrice(
            original_price=db_data.get("price_original", 0),
            discounted_price=db_data.get("price_final", 0),
            discount_rate=db_data.get("discount_rate", 0)
        ),
        review=ProductReview(
            score=db_data.get("review_score", 0.0),
            count=db_data.get("review_count", 0),
            top_keywords=keywords_list
        ),
        description_short=db_data.get("name", ""), # Description 컬럼 부재로 name 사용
        analytics=ProductAnalytics(
            skin_type=db_data.get("analytics", {}).get("skin_type"),
            age_group=db_data.get("analytics", {}).get("age_group")
        ) if db_data.get("analytics") else None
    )
