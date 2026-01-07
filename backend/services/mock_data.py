"""
Mock Data Service
Supabase 연결 전까지 사용할 Mock 데이터 제공
"""
from models.user import CustomerProfile
from models.product import Product, ProductCategory, ProductPrice, ProductReview, ProductAnalytics
from typing import Optional


# Mock 고객 데이터
MOCK_CUSTOMERS = {
    "user_12345": CustomerProfile(
        user_id="user_12345",
        skin_type=["Dry", "Sensitive"],
        skin_concerns=["Wrinkle", "Dullness"],
        preferred_tone="Warm_Spring",
        keywords=["Vegan", "Clean_Beauty", "Anti-aging"]
    ),
    "user_67890": CustomerProfile(
        user_id="user_67890",
        skin_type=["Oily", "Combination"],
        skin_concerns=["Acne", "Pore"],
        preferred_tone="Cool_Summer",
        keywords=["Trendy", "SNS_Popular", "Budget-friendly"]
    ),
    "user_0001": CustomerProfile(
        user_id="user_0001",
        skin_type=["Dry"],
        skin_concerns=["Pore", "Sebum"],
        preferred_tone="Cool_Summer",
        keywords=["Pore_Care", "Oil_Control"]
    )
}


# Mock 상품 데이터
MOCK_PRODUCTS = {
    "SW-SERUM-001": Product(
        product_id="SW-SERUM-001",
        brand="Sulwhasoo",
        name="설화수 자음생 에센스 50ml",
        category=ProductCategory(
            major="스킨케어",
            middle="기초케어",
            small="에센스"
        ),
        price=ProductPrice(
            original_price=180000,
            discounted_price=153000,
            discount_rate=15
        ),
        review=ProductReview(
            score=4.8,
            count=2340,
            top_keywords=["보습력좋은", "탄력있는", "윤기나는"]
        ),
        description_short="피부 본연의 생명력을 일깨우는 자음생 에센스",
        analytics=ProductAnalytics(
            skin_type={"Dry": 35, "Combination": 30, "Normal": 25, "Oily": 10},
            age_group={"30s": 40, "40s": 35, "50s+": 20, "20s": 5}
        )
    ),
    "HR-CUSHION-02": Product(
        product_id="HR-CUSHION-02",
        brand="헤라",
        name="헤라 블랙 쿠션 SPF34 PA++",
        category=ProductCategory(
            major="메이크업",
            middle="페이스메이크업",
            small="쿠션"
        ),
        price=ProductPrice(
            original_price=62000,
            discounted_price=52700,
            discount_rate=15
        ),
        review=ProductReview(
            score=4.9,
            count=5680,
            top_keywords=["커버력좋은", "지속력좋은", "자연스러운"]
        ),
        description_short="24시간 지속되는 완벽한 커버력",
        analytics=ProductAnalytics(
            skin_type={"Combination": 40, "Oily": 30, "Dry": 20, "Normal": 10},
            age_group={"20s": 45, "30s": 35, "40s": 15, "50s+": 5}
        )
    ),
    "HR-FOUNDATION-01": Product(
        product_id="HR-FOUNDATION-01",
        brand="헤라",
        name="헤라 실키 스테이 파운데이션 30g",
        category=ProductCategory(
            major="메이크업",
            middle="페이스메이크업",
            small="파운데이션"
        ),
        price=ProductPrice(
            original_price=68000,
            discounted_price=57800,
            discount_rate=15
        ),
        review=ProductReview(
            score=4.9,
            count=1240,
            top_keywords=["커버력좋은", "지속력좋은", "화사한"]
        ),
        description_short="24시간 무너짐 없는 실키 피부 표현"
    )
}


def get_mock_customer(user_id: str) -> Optional[CustomerProfile]:
    """
    Mock 고객 데이터 조회
    
    Args:
        user_id: 고객 ID
        
    Returns:
        CustomerProfile 또는 None
    """
    return MOCK_CUSTOMERS.get(user_id)


def get_mock_product(product_id: str) -> Optional[Product]:
    """
    Mock 상품 데이터 조회
    
    Args:
        product_id: 상품 ID
        
    Returns:
        Product 또는 None
    """
    return MOCK_PRODUCTS.get(product_id)


def recommend_product_for_customer(customer: CustomerProfile) -> Product:
    """
    고객 정보 기반 간단한 상품 추천 로직 (Mock)
    
    Args:
        customer: 고객 프로필
        
    Returns:
        추천 상품
    """
    # 간단한 추천 로직: 피부타입 기반
    if "Dry" in customer.skin_type:
        # 건성 피부 → 설화수 에센스
        return MOCK_PRODUCTS["SW-SERUM-001"]
    else:
        # 그 외 -> 헤라 쿠션
        return MOCK_PRODUCTS["HR-CUSHION-02"]
