```
"""
Info Retrieval Node
필요한 정보 수집 (상품 추천, 브랜드 톤앤매너)
"""
from typing import TypedDict, Optional, List
from services.recsys.engine import get_recommendation
from services.recsys.models import CustomerProfile as RecsysCustomerProfile
from models.user import CustomerProfile


class GraphState(TypedDict):
    """LangGraph State 정의"""
    user_id: str
    user_data: CustomerProfile
    intention: str
    recommended_brand: List[str]  # orchestrator에서 결정된 추천 브랜드
    strategy: int  # orchestrator에서 결정된 케이스 (1-4)
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


async def call_internal_recsys(
    user_id: str, 
    case: int,
    user_data: RecsysCustomerProfile,
    target_brands: Optional[List[str]] = None
) -> Optional[dict]:
    """
    내부 추천 엔진을 직접 호출합니다 (체이닝).
    """
    class MockRequest:
        def __init__(self, user_id, case, target_brand, user_data):
            self.user_id = user_id
            self.case = case
            self.target_brand = target_brand
            self.user_data = user_data

    request_data = MockRequest(user_id, case, target_brands, user_data)
    
    try:
        result = await get_recommendation(request_data)
        return result
    except Exception as e:
        print(f"❌ 내부 추천 엔진 호출 실패: {e}")
        return None

async def info_retrieval_node(state: GraphState) -> GraphState:
    """
    Info Retrieval Node
    
    메시지 생성에 필요한 정보를 수집합니다:
    - 추천 상품 정보 (RecSys API 또는 Mock)
    - 브랜드 톤앤매너
    
    Args:
        state: LangGraph State
        
    Returns:
        업데이트된 GraphState
    """
    user_data = state["user_data"]
    strategy_case = state["strategy"]  # orchestrator에서 결정한 케이스
    target_brands = state.get("recommended_brand", None)  # orchestrator에서 결정한 브랜드
    
    print("🔍 Info Retrieval 시작...")
    print(f"  - Strategy Case: {strategy_case}")
    print(f"  - Target Brands: {target_brands}")
    
    # 1. RecSys API 호출 (동기 방식)
    recommendation = call_recsys_api(
        user_id=state["user_id"],
        case=strategy_case,  # orchestrator의 case 사용
        user_data=user_data,
        target_brands=target_brands
    )
    
    if recommendation and "product_data" in recommendation:
        print(f"  ✅ RecSys 추천: {recommendation['product_name']} (ID: {recommendation['product_id']})")
        print(f"  📊 Score: {recommendation['score']}, 이유: {recommendation['reason']}")
        print(f"  - 브랜드: {recommendation['product_data']['brand']}")
        
        # RecSys API에서 받은 product_data를 바로 사용
        state["recommended_product_id"] = recommendation['product_id']
        state["product_data"] = recommendation['product_data']
        
    else:
        # RecSys 실패 시 기존 Mock 로직 사용
        print("  ⚠️ RecSys API 호출 실패 또는 product_data 없음, Mock 데이터 사용")
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