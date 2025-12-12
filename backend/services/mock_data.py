"""
Mock Data Service
Supabase 연결 전까지 사용할 Mock 데이터 제공
"""
from models.user import (
    CustomerProfile, LastPurchase, ShoppingBehavior, 
    CouponProfile, LastEngagement, PurchaseHistoryItem
)
from models.product import Product, ProductCategory, ProductPrice, ProductReview, ProductAnalytics
from models.brand import BrandProfile
from typing import Optional


# Mock 고객 데이터
MOCK_CUSTOMERS = {
    "user_12345": CustomerProfile(
        user_id="user_12345",
        name="김아모레",
        age_group="30s",
        gender="F",
        membership_level="VVIP",
        skin_type=["Dry", "Sensitive"],
        skin_concerns=["Wrinkle", "Dullness"],
        preferred_tone="Warm_Spring",
        keywords=["Vegan", "Clean_Beauty", "Anti-aging"],
        acquisition_channel="Instagram_Ad",
        average_order_value=150000,
        average_repurchase_cycle_days=45,
        repurchase_cycle_alert=True,
        last_purchase=LastPurchase(
            date="2024-10-01",
            product_id="SW-SERUM-001",
            product_name="설화수 자음생 에센스"
        ),
        purchase_history=[
            PurchaseHistoryItem(
                brand="Sulwhasoo",
                category="Serum",
                purchase_date="2024-10-01"
            ),
            PurchaseHistoryItem(
                brand="Hera",
                category="Lip",
                purchase_date="2024-08-15"
            )
        ],
        shopping_behavior=ShoppingBehavior(
            event_participation="High",
            cart_abandonment_rate="Frequent",
            price_sensitivity="Medium"
        ),
        coupon_profile=CouponProfile(
            history=["WELCOME_10", "BDAY_2024"],
            propensity="Discount_Seeker",
            preferred_type="Percentage_Off"
        ),
        last_engagement=LastEngagement(
            visit_date="2024-11-20",
            click_date="2024-11-20",
            last_visit_category="Eye Cream"
        ),
        cart_items=[],
        recently_viewed_items=["설화수 자음생 크림", "헤라 센슈얼 파우더 매트"]
    ),
    "user_67890": CustomerProfile(
        user_id="user_67890",
        name="박뷰티",
        age_group="20s",
        gender="F",
        membership_level="Gold",
        skin_type=["Oily", "Combination"],
        skin_concerns=["Acne", "Pore"],
        preferred_tone="Cool_Summer",
        keywords=["Trendy", "SNS_Popular", "Budget-friendly"],
        acquisition_channel="Naver_Search",
        average_order_value=80000,
        average_repurchase_cycle_days=60,
        repurchase_cycle_alert=False,
        last_purchase=LastPurchase(
            date="2024-09-15",
            product_id="HR-CUSHION-02",
            product_name="헤라 블랙 쿠션"
        ),
        purchase_history=[
            PurchaseHistoryItem(
                brand="Hera",
                category="Foundation",
                purchase_date="2024-09-15"
            )
        ],
        shopping_behavior=ShoppingBehavior(
            event_participation="Medium",
            cart_abandonment_rate="Occasional",
            price_sensitivity="High"
        ),
        coupon_profile=CouponProfile(
            history=["FIRST_ORDER"],
            propensity="Discount_Seeker",
            preferred_type="Percentage_Off"
        ),
        last_engagement=LastEngagement(
            visit_date="2024-12-01",
            click_date="2024-12-01",
            last_visit_category="Makeup"
        ),
        cart_items=[],
        recently_viewed_items=["헤라 립스틱", "라네즈 워터 뱅크"]
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
        brand="Hera",
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
        brand="Hera",
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


# Mock 브랜드 데이터
MOCK_BRANDS = {
    "Sulwhasoo": BrandProfile(
        brand_name="Sulwhasoo",
        target_demographic="40대+ 프리미엄 고객",
        tone_manner_style="sophisticated",
        tone_manner_examples=[
            "김아모레 고객님, 세월의 지혜가 담긴 설화수와 함께 피부 본연의 아름다움을 되찾으세요.",
            "자연에서 얻은 귀한 성분으로 정성껏 빚어낸 설화수의 가치를 경험하시기 바랍니다.",
            "VVIP 고객님께 특별한 혜택을 준비했습니다. 한 해 동안 보내주신 사랑에 감사드리며, 더욱 빛나는 피부를 위한 프리미엄 케어를 제안드립니다."
        ]
    ),
    "Hera": BrandProfile(
        brand_name="Hera",
        target_demographic="20-30대 트렌디한 여성",
        tone_manner_style="youthful",
        tone_manner_examples=[
            "박뷰티 님! 헤라의 신상품이 도착했어요. 지금 바로 확인해보세요!",
            "완벽한 메이크업의 시작, 헤라 블랙 쿠션으로 하루종일 빛나는 피부를 완성하세요.",
            "고객님만을 위한 특별 할인! 이번 기회를 놓치지 마세요 💄"
        ]
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


def get_mock_brand(brand_name: str) -> Optional[BrandProfile]:
    """
    Mock 브랜드 데이터 조회
    
    Args:
        brand_name: 브랜드명
        
    Returns:
        BrandProfile 또는 None
    """
    return MOCK_BRANDS.get(brand_name)


def recommend_product_for_customer(customer: CustomerProfile) -> Product:
    """
    고객 정보 기반 간단한 상품 추천 로직 (Mock)
    
    Args:
        customer: 고객 프로필
        
    Returns:
        추천 상품
    """
    # 간단한 추천 로직: 연령대와 피부타입 기반
    if customer.age_group in ["40s", "50s+"] and "Dry" in customer.skin_type:
        # 40대 이상 건성 피부 → 설화수 에센스
        return MOCK_PRODUCTS["SW-SERUM-001"]
    elif customer.age_group in ["20s", "30s"]:
        # 20-30대 → 헤라 쿠션
        return MOCK_PRODUCTS["HR-CUSHION-02"]
    else:
        # 기본 추천
        return MOCK_PRODUCTS["HR-FOUNDATION-01"]
