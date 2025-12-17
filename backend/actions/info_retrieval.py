"""
Info Retrieval Node
필요한 정보 수집 (상품 추천, 브랜드 톤앤매너)
"""
from typing import TypedDict
from services.mock_data import get_mock_product, get_mock_brand, recommend_product_for_customer
from models.user import CustomerProfile


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


def info_retrieval_node(state: GraphState) -> GraphState:
    """
    Info Retrieval Node
    
    메시지 생성에 필요한 정보를 수집합니다:
    - 추천 상품 정보
    - 브랜드 톤앤매너
    
    Args:
        state: LangGraph State
        
    Returns:
        업데이트된 GraphState
    """
    user_data = state["user_data"]
    
    # 1. 상품 추천 (외부 API 호출 시도 후 실패 시 Mock 사용)
    recommended_product = recommend_product_for_customer(user_data)
    

    # 2. 브랜드 톤앤매너 조회
    brand_profile = get_mock_brand(recommended_product.brand)
    
    # 3. State 업데이트
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
    
    if brand_profile:
        state["brand_tone"] = {
            "brand_name": brand_profile.brand_name,
            "tone_manner_style": brand_profile.tone_manner_style,
            "tone_manner_examples": brand_profile.tone_manner_examples,
        }
    else:
        # 브랜드 정보가 없으면 기본값 설정
        state["brand_tone"] = {
            "brand_name": recommended_product.brand,
            "tone_manner_style": "Friendly",
            "tone_manner_examples": [],
        }
    
    return state
