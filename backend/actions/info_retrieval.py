"""
Info Retrieval Node
필요한 정보 수집 (상품 추천, 브랜드 톤앤매너)
"""
from typing import TypedDict, Optional, List
from models.user import CustomerProfile
from models.product import Product, ProductCategory, ProductPrice, ProductReview, ProductAnalytics
import httpx
import json
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
    crm_reason: str = ""       # CRM 발송 이유 (예: 날씨, 할인행사, 일반홍보)
    weather_detail: str = ""   # 날씨 상세 (crm_reason이 '날씨'일 때 사용. 예: 폭염 주의보, 장마철 습기)
    target_brand: str = ""     # 선택된 브랜드 (없으면 빈 문자열)
    compliance_passed: bool
    retry_count: int
    error: str
    error_reason: str  # Compliance 실패 이유
    success: bool  # API 응답용
    retrieved_legal_rules: list  # 캐싱용: Compliance 노드에서 한 번 검색한 규칙 재사용


def _convert_dict_to_product(data: dict) -> Optional[Product]:
    """Dict 데이터를 Product 모델로 변환"""
    try:
        # DB에서 JSON으로 저장된 필드들이 문자열로 올 수 있으므로 파싱
        def parse_json_field(field_value):
            if isinstance(field_value, str):
                try:
                    return json.loads(field_value)
                except:
                    return None
            return field_value

        category = parse_json_field(data.get('category'))
        price = parse_json_field(data.get('price'))
        review = parse_json_field(data.get('review'))
        analytics = parse_json_field(data.get('analytics'))

        return Product(
            product_id=str(data.get('id') or data.get('product_id')), 
            brand=data.get('brand'),
            name=data.get('name'),
            description_short=data.get('description_short') or data.get('name'),
            category=ProductCategory(**category) if category else None,
            price=ProductPrice(**price) if price else None,
            review=ProductReview(**review) if review else None,
            analytics=ProductAnalytics(**analytics) if analytics else None
        )
    except Exception as e:
        print(f"⚠️ Product 변환 실패: {e}")
        return None


def get_recommendation_from_api(user_id: str, user_data: CustomerProfile, target_brands: list = [], reason: str = "") -> Optional[Product]:
    """
    실제 RecSys API를 호출하여 추천 상품을 가져옵니다.
    실패 시 None 반환.
    """
    try:
        url = settings.RecSys_API_URL
        
        payload = {
            "user_id": user_id,
            "target_brand": target_brands if target_brands else [],
            "intention": reason,
        }
        
        print(f"🤖 RecSys Request: {url} (user_id={user_id})")
        
        # 타임아웃 제거 (RecSys 연산 시간 고려)
        with httpx.Client(timeout=None) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("product_data"):
                p_data = result["product_data"]
                if not p_data.get('product_id') and result.get('product_id'):
                    p_data['product_id'] = result['product_id']
                
                print(f"✅ RecSys Success: {p_data.get('name')}")
                return _convert_dict_to_product(p_data)
            else:
                print("⚠️ RecSys returned no product_data")
                return None
                
    except Exception as e:
        print(f"❌ RecSys API Failed: {e}")
        return None


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
    recommended_brand = state.get("recommended_brand", "")
    # CRM Reason을 Intent로 사용 (키 매핑 보완)
    intent = state.get("crm_reason", "")
    
    recommended_product = None
    
    # 0. 이미 Product Data가 있는지 확인
    if product_data_input and product_data_input.get("product_id"):
        # 이미 데이터가 있으면 Fetch 생략
        brand_name = product_data_input.get("brand", "Unknown")
        # ID 동기화
        if not recommended_product_id:
            state["recommended_product_id"] = product_data_input.get("product_id")
    else:
        # 1. 상품 식별 (RecSys API 우선, Input ID 차순)
        if recommended_product_id:
            # Input으로 ID가 주어졌다면 해당 상품 조회
            from services.supabase_client import supabase_client
            product_data_raw = supabase_client.get_product(recommended_product_id)
            
            recommended_product = convert_db_to_product_model(product_data_raw)
          
        else:
            # ID가 없으면 RecSys API 호출
            recommended_product = call_recsys_api(user_data, recommended_brand, intent)
        
        # 새로 조회된 경우 Brand Name 추출
        if recommended_product:
            brand_name = recommended_product.brand
        else:
            # 추천 상품이 없는 경우 처리 (예: 기본 브랜드 설정 또는 에러)
            print("⚠️ Recommended product is None. Using default or target brand.")
            # target_brand가 있으면 그것을 사용, 없으면 Unknown
            if isinstance(recommended_brand, list) and recommended_brand:
                brand_name = recommended_brand[0]
            elif isinstance(recommended_brand, str) and recommended_brand:
                brand_name = recommended_brand
            else:
                brand_name = "Unknown"
    
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


def call_recsys_api(user_data, target_brand: str = "", intent: str = ""):
    """
    RecSys API를 호출하여 상품 추천 받기
    
    Args:
        user_data: CustomerProfile 객체
        target_brand: 추천 브랜드 (빈 문자열이면 모든 브랜드)
        intent: 추천 의도 ("": regular, "event": 할인율 높은 제품, "weather": 날씨별 제품)
        
    Returns:
        Product 객체 또는 Mock fallback
    """
    try:
        # RecSys API 호출
        recsys_url = settings.RecSys_API_URL
        
        # target_brand가 리스트인지 확인하고 payload 구성
        if isinstance(target_brand, list):
            brand_payload = target_brand
        elif isinstance(target_brand, str) and target_brand:
            brand_payload = [target_brand]
        else:
            brand_payload = []

        payload = {
            "user_id": user_data.user_id,
            # "user_data": user_data.model_dump(), 
            "target_brand": brand_payload,
            "intention": intent if intent else ""
        }
        
        print(f"[RecSys API] Calling {recsys_url} with intent={intent}, brand={target_brand}")
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(recsys_url, json=payload)
            response.raise_for_status()
            result = response.json()
        
        print(f"[RecSys API] Success: {result.get('product_name')} (ID: {result.get('product_id')})")
        
        # 추천 실패 시 처리 (ID가 UNKNOWN인 경우)
        if result.get('product_id') == "UNKNOWN":
            print("[RecSys API] Recommendation failed (UNKNOWN product). Returning None.")
            return None

        # RecSys API 응답을 Product 객체로 변환
        product_data = result.get("product_data", {})
        from models.product import Product, ProductCategory, ProductPrice, ProductReview
        
        return Product(
            product_id=product_data.get("product_id", result.get("product_id", "UNKNOWN")),
            brand=product_data.get("brand", "Unknown"),
            name=product_data.get("name", result.get("product_name", "Unknown Product")),
            category=ProductCategory(
                major=product_data.get("category", {}).get("major", ""),
                middle=product_data.get("category", {}).get("middle", ""),
                small=product_data.get("category", {}).get("small", "")
            ),
            price=ProductPrice(
                original_price=product_data.get("price", {}).get("original_price", 0),
                discounted_price=product_data.get("price", {}).get("discounted_price", 0),
                discount_rate=product_data.get("price", {}).get("discount_rate", 0)
            ),
            review=ProductReview(
                score=product_data.get("review", {}).get("score", 0.0),
                count=product_data.get("review", {}).get("count", 0),
                top_keywords=product_data.get("review", {}).get("top_keywords", [])
            ),
            description_short=product_data.get("description_short", result.get("product_name", ""))
        )
        
    except Exception as e:
        print(f"[RecSys API] Error: {e}")
        # RecSys 호출 실패시 None 반환 (Graph에서 처리)
        return None


def convert_db_to_product_model_old(db_data: dict):
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
