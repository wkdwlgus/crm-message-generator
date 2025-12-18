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
    
    # Application Settings
    max_retry_count: int = 5
    env: str = "development"

    SUPABASE_URL: str
    SUPABASE_KEY: str

    RecSys_API_URL: str = "http://localhost:8001/recommend"
    
    # CORS
    allowed_origins: str = "http://localhost:5173"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """CORS allowed origins를 리스트로 변환"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()
