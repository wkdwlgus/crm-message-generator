"""
Configuration management using pydantic-settings
환경 변수 로드 및 애플리케이션 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # OpenAI API
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    
    # Supabase Settings
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Application Settings
    max_retry_count: int = 5
    env: str = "development"

    SUPABASE_URL: str
    SUPABASE_KEY: str

    RecSys_API_URL: str = "https://blooming-recsys-beta.internal.thankfulsea-77291fc5.westus3.azurecontainerapps.io/recommend"
    
    # CORS
    allowed_origins: str = "*"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """CORS allowed origins를 리스트로 변환"""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()
