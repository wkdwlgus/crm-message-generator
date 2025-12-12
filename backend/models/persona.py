"""
Persona 관련 Pydantic 모델
페르소나 데이터 구조 정의
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class Persona(BaseModel):
    """고객 페르소나 - 타겟 세그먼트 정의"""
    
    persona_id: Optional[int] = Field(None, description="DB 자동 생성 ID")
    name: str = Field(..., description="페르소나 이름")
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
    
    class Config:
        json_schema_extra = {
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
