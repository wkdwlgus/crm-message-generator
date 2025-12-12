# Data Model: Persona-Based CRM Message Generation

**Feature**: 001-persona-crm-messages | **Date**: 2025-12-12  
**Purpose**: Phase 1 데이터 모델 설계 - 엔티티 및 관계 정의

## Overview

이 문서는 CRM 메시지 생성 시스템의 핵심 데이터 모델을 정의합니다. 모든 모델은 Pydantic 스키마로 구현되어 런타임 검증 및 타입 안전성을 보장합니다.

---

## 1. Customer Profile (고객 프로필)

### 설명
개별 고객의 상세 정보를 담는 핵심 엔티티. 페르소나 특성과 개인화된 메시지 생성에 필요한 모든 데이터를 포함합니다.

### Pydantic Schema

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class LastPurchase(BaseModel):
    date: str = Field(..., description="구매 날짜 (YYYY-MM-DD)")
    product_id: str
    product_name: str

class PurchaseHistoryItem(BaseModel):
    brand: str
    category: str
    purchase_date: str  # YYYY-MM-DD

class ShoppingBehavior(BaseModel):
    event_participation: str = Field(..., description="High | Medium | Low")
    cart_abandonment_rate: str = Field(..., description="Frequent | Occasional | Rare")
    price_sensitivity: str = Field(..., description="High | Medium | Low")

class CouponProfile(BaseModel):
    history: List[str] = Field(default_factory=list, description="사용한 쿠폰 코드들")
    propensity: str = Field(..., description="Discount_Seeker | Premium_Buyer | Balanced")
    preferred_type: str = Field(..., description="Percentage_Off | Fixed_Amount | Free_Shipping")

class LastEngagement(BaseModel):
    visit_date: Optional[str] = None  # YYYY-MM-DD
    click_date: Optional[str] = None  # YYYY-MM-DD
    last_visit_category: Optional[str] = None

class CartItem(BaseModel):
    id: str
    name: str
    added_at: str  # YYYY-MM-DD

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
    recently_viewed_items: List[str] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user_12345",
                "name": "김아모레",
                "age_group": "30s",
                "gender": "F",
                "membership_level": "VVIP",
                "skin_type": ["Dry", "Sensitive"],
                "skin_concerns": ["Wrinkle", "Dullness"],
                "preferred_tone": "Warm_Spring",
                "keywords": ["Vegan", "Clean_Beauty", "Anti-aging"],
                "acquisition_channel": "Instagram_Ad",
                "average_order_value": 150000,
                "average_repurchase_cycle_days": 45,
                "repurchase_cycle_alert": True,
                "last_purchase": {
                    "date": "2024-10-01",
                    "product_id": "SW-SERUM-001",
                    "product_name": "Sulwhasoo First Care Activating Serum"
                },
                "shopping_behavior": {
                    "event_participation": "High",
                    "cart_abandonment_rate": "Frequent",
                    "price_sensitivity": "Medium"
                },
                "coupon_profile": {
                    "history": ["WELCOME_10", "BDAY_2024"],
                    "propensity": "Discount_Seeker",
                    "preferred_type": "Percentage_Off"
                }
            }
        }
```

### 데이터베이스 매핑 (Supabase)

```sql
CREATE TABLE customers (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age_group VARCHAR(10) NOT NULL CHECK (age_group IN ('20s', '30s', '40s', '50s+')),
    gender CHAR(1) CHECK (gender IN ('M', 'F')),
    membership_level VARCHAR(20) CHECK (membership_level IN ('VVIP', 'VIP', 'Gold', 'Silver')),
    skin_type TEXT[] NOT NULL,
    skin_concerns TEXT[] NOT NULL,
    preferred_tone VARCHAR(50),
    keywords TEXT[],
    acquisition_channel VARCHAR(100),
    average_order_value INTEGER CHECK (average_order_value >= 0),
    average_repurchase_cycle_days INTEGER CHECK (average_repurchase_cycle_days >= 0),
    repurchase_cycle_alert BOOLEAN DEFAULT FALSE,
    shopping_behavior JSONB,  -- ShoppingBehavior 객체
    coupon_profile JSONB,  -- CouponProfile 객체
    last_engagement JSONB,  -- LastEngagement 객체
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 구매 이력은 별도 테이블로 정규화
CREATE TABLE purchase_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES customers(user_id),
    brand VARCHAR(100),
    category VARCHAR(100),
    product_id VARCHAR(50),
    product_name VARCHAR(200),
    purchase_date DATE,
    amount INTEGER,
    is_last_purchase BOOLEAN DEFAULT FALSE
);

-- 장바구니 아이템
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES customers(user_id),
    product_id VARCHAR(50),
    product_name VARCHAR(200),
    added_at TIMESTAMP
);
```

---

## 2. Persona (페르소나)

### 설명
고객 세그먼트를 대표하는 아키타입. 메시지 톤, 언어 스타일, 콘텐츠 방향성을 결정하는 데 사용됩니다.

### Pydantic Schema

```python
class Persona(BaseModel):
    """고객 페르소나 - 타겟 세그먼트 정의"""
    
    persona_id: Optional[int] = Field(None, description="DB 자동 생성 ID")
    name: str = Field(..., description="페르소나 이름 (예: Budget-Conscious Parent)")
    description: str
    
    # 인구통계
    age_range: str = Field(..., description="20-29 | 30-39 | 40-49 | 50+")
    income_level: str = Field(..., description="High | Medium | Low")
    
    # 커뮤니케이션 선호
    communication_tone: str = Field(..., description="formal | casual | friendly | sophisticated")
    detail_level: str = Field(..., description="brief | comprehensive | balanced")
    preferred_content_types: List[str] = Field(..., description="product_info | discount | tips | trends")
    
    # 관심사 및 페인포인트
    interests: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    
    created_at: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "프리미엄 안티에이징 추구자",
                "description": "40대 이상 고소득층, 고급 안티에이징 제품 선호",
                "age_range": "40-49",
                "income_level": "High",
                "communication_tone": "sophisticated",
                "detail_level": "comprehensive",
                "preferred_content_types": ["product_info", "ingredients", "research"],
                "interests": ["Anti-aging", "Premium", "Science-backed"],
                "pain_points": ["Wrinkle", "Sagging", "Dullness"]
            }
        }
```

### 데이터베이스 매핑

```sql
CREATE TABLE personas (
    persona_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    age_range VARCHAR(20),
    income_level VARCHAR(50),
    communication_tone VARCHAR(50),
    detail_level VARCHAR(50),
    preferred_content_types TEXT[],
    interests TEXT[],
    pain_points TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 3. Product (상품)

### 설명
추천 및 메시지에 포함될 상품 정보. 가격, 리뷰, 카테고리 등 상세 정보를 포함합니다.

### Pydantic Schema

```python
class ProductCategory(BaseModel):
    major: str = Field(..., description="메이크업 | 스킨케어 | 바디케어")
    middle: str = Field(..., description="페이스메이크업 | 기초케어 | 클렌징")
    small: Optional[str] = Field(None, description="파운데이션 | 토너 | 세럼")

class ProductPrice(BaseModel):
    original_price: int = Field(..., ge=0)
    discounted_price: int = Field(..., ge=0)
    discount_rate: int = Field(0, ge=0, le=100, description="할인율 (%, 정수)")

class ProductReview(BaseModel):
    score: float = Field(..., ge=0.0, le=5.0)
    count: int = Field(0, ge=0)
    top_keywords: List[str] = Field(default_factory=list, description="리뷰 키워드 Top 3")

class ProductAnalytics(BaseModel):
    """누가 구매했을까요? 통계"""
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
    
    created_at: Optional[datetime] = None
    
    class Config:
        schema_extra = {
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
```

### 데이터베이스 매핑

```sql
CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    brand VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    category_major VARCHAR(100),
    category_middle VARCHAR(100),
    category_small VARCHAR(100),
    original_price INTEGER CHECK (original_price >= 0),
    discounted_price INTEGER CHECK (discounted_price >= 0),
    discount_rate INTEGER CHECK (discount_rate >= 0 AND discount_rate <= 100),
    review_score DECIMAL(2,1) CHECK (review_score >= 0 AND review_score <= 5),
    review_count INTEGER DEFAULT 0,
    top_keywords TEXT[],
    description_short TEXT,
    analytics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_category ON products(category_major, category_middle);
```

---

## 4. Brand Profile (브랜드 프로필)

### 설명
브랜드별 톤앤매너 및 커뮤니케이션 가이드라인. GPT-5 프롬프트에 few-shot 예시로 주입됩니다.

### Pydantic Schema

```python
class BrandProfile(BaseModel):
    """브랜드 톤앤매너 프로필"""
    
    brand_id: Optional[int] = None
    brand_name: str = Field(..., description="Sulwhasoo | Hera | Laneige | etc")
    target_demographic: str = Field(..., description="타겟 고객층")
    
    tone_manner_style: str = Field(..., description="sophisticated | youthful | luxury | natural")
    tone_manner_examples: List[str] = Field(
        ..., 
        description="브랜드 톤앤매너를 보여주는 예시 메시지 3-5개"
    )
    
    created_at: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "brand_name": "Sulwhasoo",
                "target_demographic": "40대+ 프리미엄 고객",
                "tone_manner_style": "sophisticated",
                "tone_manner_examples": [
                    "김아모레 고객님, 세월의 지혜가 담긴 설화수와 함께 피부 본연의 아름다움을 되찾으세요.",
                    "자연에서 얻은 귀한 성분으로 정성껏 빚어낸 설화수의 가치를 경험하시기 바랍니다."
                ]
            }
        }
```

### 데이터베이스 매핑

```sql
CREATE TABLE brands (
    brand_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(100) UNIQUE NOT NULL,
    target_demographic VARCHAR(200),
    tone_manner_style VARCHAR(50),
    tone_manner_examples TEXT[],  -- 예시 메시지들
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. Generated Message (생성된 메시지)

### 설명
AI가 생성한 최종 메시지 및 관련 메타데이터. 감사 추적 및 최적화에 활용됩니다.

### Pydantic Schema

```python
class GeneratedMessage(BaseModel):
    """생성된 CRM 메시지"""
    
    message_id: Optional[int] = None
    user_id: str
    
    # 메시지 내용
    message_text: str
    channel: str = Field(..., description="email | sms | app_push | kakaotalk")
    
    # 생성 컨텍스트
    persona_used: Optional[str] = None
    product_id: Optional[str] = None
    brand_name: Optional[str] = None
    
    # 컴플라이언스 및 품질
    compliance_passed: bool
    retry_count: int = Field(0, ge=0)
    
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "message_id": 1001,
                "user_id": "user_12345",
                "message_text": "김아모레 고객님, VVIP 회원님을 위한 특별 혜택...",
                "channel": "email",
                "persona_used": "프리미엄 안티에이징 추구자",
                "product_id": "SW-SERUM-001",
                "brand_name": "Sulwhasoo",
                "compliance_passed": True,
                "retry_count": 0
            }
        }
```

### 데이터베이스 매핑

```sql
CREATE TABLE generated_messages (
    message_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES customers(user_id),
    message_text TEXT NOT NULL,
    channel VARCHAR(50) CHECK (channel IN ('email', 'sms', 'app_push', 'kakaotalk')),
    persona_used VARCHAR(100),
    product_id VARCHAR(50) REFERENCES products(product_id),
    brand_name VARCHAR(100),
    compliance_passed BOOLEAN NOT NULL,
    retry_count INTEGER DEFAULT 0,
    generated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_generated_messages_user_id ON generated_messages(user_id);
CREATE INDEX idx_generated_messages_generated_at ON generated_messages(generated_at DESC);
CREATE INDEX idx_generated_messages_compliance ON generated_messages(compliance_passed);
```

---

## 6. Channel Configuration (채널 설정)

### 설명
각 커뮤니케이션 채널의 제약조건 및 특성 정의.

### Pydantic Schema

```python
class ChannelConfiguration(BaseModel):
    """채널별 제약조건 및 특성"""
    
    channel_name: str = Field(..., description="email | sms | app_push | kakaotalk")
    max_length: int = Field(..., description="최대 글자 수")
    supports_html: bool = Field(False, description="HTML 지원 여부")
    requires_link: bool = Field(False, description="링크 포함 필수 여부")
    
    tone_guidelines: str = Field(..., description="채널별 톤 가이드라인")
    
    class Config:
        schema_extra = {
            "example": {
                "channel_name": "sms",
                "max_length": 70,
                "supports_html": False,
                "requires_link": True,
                "tone_guidelines": "간결하고 명확하게. 행동 유도 필수"
            }
        }

# 상수로 정의 (설정 파일)
CHANNEL_CONFIGS = {
    'sms': ChannelConfiguration(
        channel_name='sms',
        max_length=70,
        supports_html=False,
        requires_link=True,
        tone_guidelines="간결하고 명확하게. 행동 유도 필수"
    ),
    'email': ChannelConfiguration(
        channel_name='email',
        max_length=800,
        supports_html=True,
        requires_link=False,
        tone_guidelines="상세한 설명 가능. 제목과 본문 구분"
    ),
    'app_push': ChannelConfiguration(
        channel_name='app_push',
        max_length=100,
        supports_html=False,
        requires_link=False,
        tone_guidelines="즉각적 주목 필요. 긴급성 강조"
    ),
    'kakaotalk': ChannelConfiguration(
        channel_name='kakaotalk',
        max_length=1000,
        supports_html=False,
        requires_link=False,
        tone_guidelines="친근하고 대화체. 이미지 활용 가능"
    )
}
```

---

## 7. Compliance Rule (컴플라이언스 규칙)

### 설명
화장품법 등 법적 제약사항 정의. 금칙어 리스트 및 검증 규칙 포함.

### Pydantic Schema

```python
class ComplianceRule(BaseModel):
    """컴플라이언스 규칙"""
    
    rule_id: Optional[int] = None
    rule_type: str = Field(..., description="prohibited_words | required_disclaimer | format_rule")
    rule_value: str = Field(..., description="규칙 내용 (JSON 또는 텍스트)")
    description: str
    is_active: bool = Field(True)
    
    created_at: Optional[datetime] = None

# 금칙어 리스트 (설정 파일 또는 DB)
PROHIBITED_WORDS = [
    "완치", "치료", "의약", "의학", "임상",
    "최고", "세계 최초", "1등", "독보적",
    "기적", "마법", "신기", "놀라운",
    "100%", "절대", "전혀", "무조건",
    "살이 빠지는", "체지방 감소", "다이어트",
    "부작용 없음", "안전성 입증"
]
```

---

## 관계 다이어그램

```
┌─────────────────┐         ┌─────────────────┐
│  CustomerProfile│────────▶│ GeneratedMessage│
│                 │ 1     * │                 │
└─────────────────┘         └─────────────────┘
         │                           │
         │                           │
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│    Persona      │         │    Product      │
│                 │         │                 │
└─────────────────┘         └─────────────────┘
                                     │
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  BrandProfile   │
                            │                 │
                            └─────────────────┘
```

**관계 설명**:
- 1:N - Customer ↔ GeneratedMessage (한 고객이 여러 메시지 수신)
- N:1 - GeneratedMessage ↔ Product (여러 메시지가 동일 상품 추천 가능)
- N:1 - Product ↔ Brand (여러 상품이 하나의 브랜드에 속함)
- N:1 - Customer ↔ Persona (여러 고객이 동일 페르소나에 매핑 가능)

---

## 다음 단계

Phase 1의 다음 작업: **API Contracts** (`contracts/openapi.yaml`) 및 **Quickstart Guide** (`quickstart.md`) 생성
