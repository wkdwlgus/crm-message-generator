# 🌸 Blooming CRM

페르소나 기반 초개인화 CRM 메시지 생성 시스템

## 📋 프로젝트 개요

Blooming CRM은 고객의 페르소나와 구매 이력을 분석하여 개인화된 마케팅 메시지를 자동으로 생성하는 시스템입니다.

**핵심 기능:**
- 🎯 페르소나 기반 메시지 전략 수립
- 🤖 OpenAI GPT-5를 활용한 자연어 메시지 생성
- ✅ 화장품법 준수 자동 검증 (최대 5회 재시도)
- 📱 멀티채널 지원 (SMS, 카카오톡, 이메일)
- 🔄 LangGraph 기반 5-노드 워크플로우

## 🏗️ 기술 스택

### Backend
- **Framework**: FastAPI
- **AI Workflow**: LangGraph
- **LLM**: OpenAI GPT-5
- **Language**: Python 3.11+
- **Validation**: Pydantic

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS

### Database (향후 연동 예정)
- **Database**: Supabase (PostgreSQL)

## 🚀 시작하기

### 사전 요구사항
- Python 3.11 이상
- Node.js 18 이상
- OpenAI API Key

### 1. 프로젝트 클론

```bash
git clone <repository-url>
cd blooming-v1
```

### 2. Backend 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
# .env 파일 생성 후 OpenAI API Key 입력
# OPENAI_API_KEY=your-api-key-here
```

### 3. Frontend 설정

```bash
cd frontend

# 패키지 설치
npm install

# 환경변수 설정
# .env 파일 생성
# VITE_API_BASE_URL=http://localhost:8000
```

### 4. 실행

**Backend 서버 실행:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend 서버 실행:**
```bash
cd frontend
npm run dev
```

브라우저에서 http://localhost:5173 접속

## 🔍 Mock 데이터 테스트

현재 버전은 Mock 데이터를 사용합니다. 다음 테스트 사용자를 이용할 수 있습니다:

- **user_12345**: 김아모레 (VVIP, 40대, 건성/민감성)
- **user_67890**: 박뷰티 (Gold, 20대, 지성/복합성)

## 📚 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🏗️ 아키텍처

### LangGraph 워크플로우
```
Orchestrator (전략 수립)
    ↓
Info Retrieval (상품 추천 + 브랜드 톤)
    ↓
Message Writer (GPT-5 메시지 생성)
    ↓
Compliance Check (화장품법 검증)
    ↓ (실패 시 재시도)
Return Response (최종 응답)
```

## 📁 프로젝트 구조

```
blooming-v1/
├── frontend/          # React + TypeScript + Vite + Tailwind CSS
├── backend/           # Python + FastAPI + LangGraph
│   ├── actions/       # LangGraph 노드
│   ├── api/           # FastAPI 라우터
│   ├── models/        # Pydantic 모델
│   ├── services/      # Mock 데이터 서비스
│   ├── config.py      # 환경 설정
│   ├── graph.py       # LangGraph 워크플로우
│   └── main.py        # FastAPI 앱
└── README.md
```

## 📝 향후 계획

- [ ] Supabase 데이터베이스 연동
- [ ] 사용자 인증 및 권한 관리
- [ ] 메시지 히스토리 저장 및 조회
- [ ] A/B 테스트 기능
- [ ] 성능 지표 대시보드
- [ ] 배포 자동화 (Docker, CI/CD)

## 📄 라이선스

MIT License

## 👥 기여자

- 개발자: [Your Name]

