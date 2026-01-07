"""
Customer Profile 관련 Pydantic 모델
고객 프로필 데이터 구조 정의
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class CustomerProfile(BaseModel):
    """고객 프로필 - 페르소나 기반 메시지 생성의 기초 데이터"""
    
    # 기본 정보
    user_id: str = Field(..., description="고유 사용자 ID")
    name: str = Field("00", description="고객 이름")
    age_group: str = Field("Unknown", description="20s, 30s, 40s etc")
    membership_level: str = Field("General", description="VIP, General, New")
    
    # 멤버십 및 피부 정보
    skin_type: List[str] = Field(..., description="Dry, Oily, Combination, Sensitive")
    skin_concerns: List[str] = Field(..., description="Wrinkle, Dullness, Acne, Pore")
    preferred_tone: Optional[str] = Field(None, description="Warm_Spring | Cool_Summer | etc")
    
    # 관심사 및 키워드
    keywords: List[str] = Field(..., description="Vegan, Clean_Beauty, Anti-aging, etc")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_12345",
                "skin_type": ["Dry", "Sensitive"],
                "skin_concerns": ["Wrinkle", "Dullness"],
                "preferred_tone": "Warm_Spring",
                "keywords": ["Vegan", "Clean_Beauty", "Anti-aging"]
            }
        }
