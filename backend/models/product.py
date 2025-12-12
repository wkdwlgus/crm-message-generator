"""
Product 관련 Pydantic 모델
상품 정보 데이터 구조 정의
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ProductCategory(BaseModel):
    """상품 카테고리"""
    major: str = Field(..., description="메이크업 | 스킨케어 | 바디케어")
    middle: str = Field(..., description="페이스메이크업 | 기초케어 | 클렌징")
    small: Optional[str] = Field(None, description="파운데이션 | 토너 | 세럼")


class ProductPrice(BaseModel):
    """상품 가격 정보"""
    original_price: int = Field(..., ge=0)
    discounted_price: int = Field(..., ge=0)
    discount_rate: int = Field(0, ge=0, le=100, description="할인율 (%, 정수)")


class ProductReview(BaseModel):
    """상품 리뷰 정보"""
    score: float = Field(..., ge=0.0, le=5.0)
    count: int = Field(0, ge=0)
    top_keywords: List[str] = Field(default_factory=list, description="리뷰 키워드 Top 3")


class ProductAnalytics(BaseModel):
    """상품 구매 통계 - 누가 구매했을까요?"""
    skin_type: Optional[dict] = Field(None, description="피부타입별 구매 비율")
    age_group: Optional[dict] = Field(None, description="연령대별 구매 비율")


class Product(BaseModel):
    """상품 정보"""
    
    product_id: str
    brand: str
    name: str
    
    category: ProductCategory
    price: ProductPrice
    review: ProductReview
    
    description_short: str = Field(..., description="한 줄 설명")
    analytics: Optional[ProductAnalytics] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "11204234",
                "brand": "Hera",
                "name": "실키 스테이 파운데이션 30g",
                "category": {
                    "major": "메이크업",
                    "middle": "페이스메이크업",
                    "small": "파운데이션"
                },
                "price": {
                    "original_price": 68000,
                    "discounted_price": 57800,
                    "discount_rate": 15
                },
                "review": {
                    "score": 4.9,
                    "count": 1240,
                    "top_keywords": ["커버력좋은", "지속력좋은", "화사한"]
                },
                "description_short": "24시간 무너짐 없는 실키 피부 표현"
            }
        }
