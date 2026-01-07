"""
Blooming CRM Message Generation System
페르소나 기반 초개인화 CRM 메시지 생성 시스템
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from api.message import router as message_router

# FastAPI 앱 생성
app = FastAPI(
    title="Blooming CRM API",
    description="페르소나 기반 초개인화 CRM 메시지 생성 시스템",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(message_router, tags=["Message Generation"])


@app.get("/", tags=["Health"])
async def root():
    """
    Health Check 엔드포인트
    """
    return {
        "service": "Blooming CRM API",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.on_event("startup")
async def startup_event():
    """
    애플리케이션 시작 시 실행
    """
    print("🌸 Blooming CRM API 서버가 시작되었습니다.")
    print(f"Environment: {settings.env}")
    print(f"OpenAI Model: {settings.openai_model}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    애플리케이션 종료 시 실행
    """
    print("🌸 Blooming CRM API 서버가 종료됩니다.")


    
