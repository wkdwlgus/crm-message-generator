"""
Brand Profile 관련 Pydantic 모델
브랜드 톤앤매너 데이터 구조 정의
"""
from pydantic import BaseModel, Field
from typing import List, Optional


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
    
    class Config:
        json_schema_extra = {
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
