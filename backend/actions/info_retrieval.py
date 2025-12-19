"""
Info Retrieval Node
필요한 정보 수집 (상품 추천, 브랜드 톤앤매너)
"""
from typing import TypedDict, Optional, List
from services.mock_data import get_mock_product, get_mock_brand, recommend_product_for_customer
from models.user import CustomerProfile
import httpx


class GraphState(TypedDict):
    """LangGraph State 정의"""
    user_id: str
    user_data: CustomerProfile
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
    retrieved_legal_rules: list  # 캐싱용: Compliance 노드에서 한 번 검색한 규칙 재사용


# RecSys API 설정
RECSYS_API_URL = "http://localhost:8001/recommend"


def call_recsys_api(
    user_id: str, 
    case: int,  # orchestrator에서 전달받은 case 사용
    user_data: CustomerProfile,
    target_brands: Optional[List[str]] = None
) -> Optional[dict]:
    """
    RecSys API를 호출하여 상품 추천을 받습니다.
    
    Args:
        user_id: 사용자 ID
        case: orchestrator에서 결정한 전략 케이스 (1-4)
        user_data: CustomerProfile 객체
        target_brands: 필터링할 브랜드 리스트
        
    Returns:
        추천 결과 dict {product_id, product_name, score, reason} 또는 None
    """
    payload = {
        "user_id": user_id,
        "case": case,
        "target_brand": target_brands,
        "user_data": user_data.dict() if case > 1 else None
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(RECSYS_API_URL, json=payload)
            response.raise_for_status()
            # 명시적으로 UTF-8 인코딩 설정
            response.encoding = 'utf-8'
            result = response.json()
            print(f"  [DEBUG] Response keys: {list(result.keys()) if result else 'None'}")
            print(f"  [DEBUG] Has product_data: {'product_data' in result if result else False}")
            if result and 'product_data' in result:
                print(f"  [DEBUG] product_data brand: {result['product_data'].get('brand', 'N/A')}")
            return result
    except httpx.HTTPError as e:
        print(f"❌ RecSys API 호출 실패: {e}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None


def info_retrieval_node(state: GraphState) -> GraphState:
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
        print(f"  🛍️ 상품 데이터 로드 완료, {recommendation['product_data']['brand']}")
        state["brand_tone"] = recommendation['product_data']['brand']
        print(f"  🎨 브랜드 톤앤매너 로드: {state['brand_tone']}")
        
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