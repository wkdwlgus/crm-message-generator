"""
Info Retrieval Node
필요한 정보 수집 (상품 추천, 브랜드 톤앤매너)
"""
from typing import TypedDict, Optional, List, Dict, Any
from services.mock_data import recommend_product_for_customer
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
    target_brands = state.get("recommended_brand", None)
    
    # RecSys API URL
    RECSYS_API_URL = "http://localhost:8001/recommend"
    
    print(f"  🎯 상품 추천 시작 (RecSys API 호출)")
    print(f"  - User ID: {state['user_id']}")
    print(f"  - Target Brands: {target_brands}")
    
    # RecSys API 호출
    # orchestrator에서 전달받은 리스트(또는 문자열)를 RecSys API 포맷에 맞게 전송
    raw_brands = state.get("recommended_brand", [])
    if isinstance(raw_brands, str):
        target_brands_list = [raw_brands]
    elif isinstance(raw_brands, list):
        target_brands_list = raw_brands
    else:
        target_brands_list = []

    payload = {
        "user_id": state["user_id"],
        "user_data": user_data.dict() if user_data else None,
        "target_brand": target_brands_list,
        "intention": state.get("crm_reason", "")   # backend 'crm_reason' -> RecSys 'intention' 매핑
    }
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(RECSYS_API_URL, json=payload)
            response.raise_for_status()
            response.encoding = 'utf-8'
            result = response.json()
            
            if result and 'product_data' in result:
                print(f"  ✅ RecSys API 추천 성공: {result['product_name']} (ID: {result['product_id']})")
                print(f"  📊 Score: {result.get('score', 0.0):.4f}")
                print(f"  - 브랜드: {result['product_data']['brand']}")
                
                state["recommended_product_id"] = result['product_id']
                state["product_data"] = result['product_data']
                state["brand_tone"] = result['product_data']['brand']
                print(f"  🛍️ 상품 데이터 로드 완료")
                return state
            else:
                print(f"  ⚠️ RecSys API 응답에 product_data가 없음")
                
    except httpx.HTTPError as e:
        print(f"  ❌ RecSys API 호출 실패: {e}")
    except Exception as e:
        print(f"  ❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 추천 실패 시 Mock 데이터로 fallback
    print("  ⚠️ RecSys API 실패, Mock 데이터 사용")
    recommended_product = recommend_product_for_customer(user_data)
    
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
    
    return state