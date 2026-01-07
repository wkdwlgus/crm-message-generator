"""
Generated Message 관련 Pydantic 모델
메시지 생성 결과 및 응답 데이터 구조 정의
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


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


class MessageRequest(BaseModel):
    """API 요청 모델 - POST /message"""
    userId: str
    channel: str = Field(..., description="SMS | APPPUSH | KAKAO | EMAIL")
    intention: Optional[str] = Field(None, description="CRM 발송 이유 (날씨, 할인행사 등)")
    hasBrand: Optional[bool] = False
    targetBrand: Optional[str] = None
    season: Optional[str] = None
    weatherDetail: Optional[str] = None
    beautyProfile: Optional[dict] = None
    userPrompt: Optional[str] = None
    persona: Optional[str] = None


class MessageResponse(BaseModel):
    """API 응답 모델 - GET/POST /message"""
    message: str = Field(..., description="생성된 CRM 메시지 텍스트")
    user: str = Field(..., description="요청한 고객 ID")
    method: str = Field(..., description="email | sms | app_push | kakaotalk")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "김아모레 고객님, VVIP 회원님만을 위한 특별한 소식...",
                "user": "user_12345",
                "method": "email"
            }
        }


class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    error: str = Field(..., description="오류 메시지")
    user: Optional[str] = Field(None, description="요청한 고객 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "User not found: user_99999",
                "user": "user_99999"
            }
        }
