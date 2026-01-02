from pydantic import BaseModel, Field
from typing import List, Optional

class LastPurchase(BaseModel):
    """마지막 구매 정보"""
    date: str = Field(..., description="구매 날짜 (YYYY-MM-DD)")
    product_id: str
    product_name: str


class PurchaseHistoryItem(BaseModel):
    """구매 이력 항목"""
    brand: str
    category: str
    purchase_date: str  # YYYY-MM-DD


class ShoppingBehavior(BaseModel):
    """쇼핑 행동 패턴"""
    event_participation: str = Field(..., description="High | Medium | Low")
    cart_abandonment_rate: str = Field(..., description="Frequent | Occasional | Rare")
    price_sensitivity: str = Field(..., description="High | Medium | Low")


class CouponProfile(BaseModel):
    """쿠폰 사용 프로필"""
    history: List[str] = Field(default_factory=list, description="사용한 쿠폰 코드들")
    propensity: str = Field(..., description="Discount_Seeker | Premium_Buyer | Balanced")
    preferred_type: str = Field(..., description="Percentage_Off | Fixed_Amount | Free_Shipping")


class LastEngagement(BaseModel):
    """최근 참여 활동"""
    visit_date: Optional[str] = None  # YYYY-MM-DD
    click_date: Optional[str] = None  # YYYY-MM-DD
    last_visit_category: Optional[str] = None


class CartItem(BaseModel):
    """장바구니 아이템"""
    id: str
    name: str
    brand: Optional[str] = None
    added_at: str  # YYYY-MM-DD


class RecentlyViewedItem(BaseModel):
    """최근 본 상품"""
    id: str
    name: str
    brand: Optional[str] = None


class CustomerProfile(BaseModel):
    """고객 프로필 - 페르소나 기반 메시지 생성의 기초 데이터"""
    
    # 기본 정보
    user_id: str = Field(..., description="고유 사용자 ID")
    name: str
    age_group: str = Field(..., description="20s | 30s | 40s | 50s+")
    gender: str = Field(..., description="M | F")
    
    # 멤버십 및 피부 정보
    membership_level: str = Field(..., description="VVIP | VIP | Gold | Silver")
    skin_type: List[str] = Field(..., description="Dry, Oily, Combination, Sensitive")
    skin_concerns: List[str] = Field(..., description="Wrinkle, Dullness, Acne, Pore")
    preferred_tone: Optional[str] = Field(None, description="Warm_Spring | Cool_Summer | etc")
    
    # 관심사 및 키워드
    keywords: List[str] = Field(..., description="Vegan, Clean_Beauty, Anti-aging, etc")
    
    # 구매 이력
    acquisition_channel: str
    average_order_value: int = Field(..., ge=0, description="평균 구매 금액")
    average_repurchase_cycle_days: int = Field(..., ge=0, description="평균 재구매 주기 (일)")
    repurchase_cycle_alert: bool = Field(False, description="재구매 주기 도래 알림")
    
    last_purchase: Optional[LastPurchase] = None
    purchase_history: List[PurchaseHistoryItem] = Field(default_factory=list)
    
    # 행동 데이터
    shopping_behavior: ShoppingBehavior
    coupon_profile: CouponProfile
    
    # 최근 활동
    last_engagement: LastEngagement
    cart_items: List[CartItem] = Field(default_factory=list)
    recently_viewed_items: List[RecentlyViewedItem] = Field(default_factory=list)
