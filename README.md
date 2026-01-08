# 🌸 Blooming CRM

페르소나 기반 초개인화 CRM 메시지 생성 및 타겟팅 시스템

## 📋 프로젝트 개요

Blooming CRM은 마케터가 설정한 **페르소나**를 기반으로 잠재 고객을 자동으로 추출하고, 고객의 특성(피부 타입, 고민 등)에 맞춘 개인화 마케팅 메시지를 생성하는 AI 시스템입니다.

**핵심 기능:**
- 🎯 **페르소나 기반 타겟팅**: 특정 페르소나와 유사한 속성을 가진 고객군(User IDs)을 데이터베이스에서 자동 추출
- ✍️ **초개인화 메시지 생성**: 고객 정보 + 선호 키워드 + 추천 제품 정보를 결합한 1:1 메시지 작성
- 🤖 **AI 에이전트 워크플로우**: LangGraph를 활용한 체계적인 메시지 생성 파이프라인 (검색 -> 생성 -> 검수)
- ✅ **화장품법 자동 준수**: 생성된 메시지가 광고 법규를 위반하지 않는지 AI가 자동 검토 및 수정
- 🛒 **제품 추천 연동**: RecSys 엔진과 연동하여 고객별 맞춤형 제품 추천 포함

## 🏗️ 기술 스택

### Architecture
- **Monorepo Structure**: Frontend, Backend, RecSys

### Backend (`/backend`)
- **Framework**: FastAPI
- **Agent Orchestration**: LangGraph (StateGraph)
- **LLM**: OpenAI GPT-4o / GPT-4o-mini
- **Database**: Supabase (PostgreSQL) - 고객 데이터 및 로그 저장
- **Validation**: Pydantic

### Frontend (`/frontend`)
- **Framework**: React 18 + TypeScript
- **State Management**: Zustand
- **Build Tool**: Vite
- **Styling**: Tailwind CSS

### Recommendation System (`/RecSys`)
- **Model**: Cross-Encoder 기반 추천 모델
- **Features**: Intent 기반 필터링 (Regular/Event)

## 🔄 시스템 워크플로우

1. **페르소나 정의**: 마케터가 타겟 페르소나(예: "30대 건성 피부")를 설정합니다.
2. **타겟 오디언스 추출 (Orchestrator)**: Supabase에서 해당 페르소나와 일치하는 고객 ID 목록을 추출합니다.
3. **정보 검색 (Info Retrieval)**:
   - CRM 데이터 조회 (고객 이름, 피부 고민 등)
   - 제품 추천 (RecSys API 호출)
   - 마케팅 가이드라인 참조
4. **메시지 작성 (Message Writer)**: LLM이 수집된 정보를 바탕으로 채널(운 문자, 카카오톡 등)에 맞는 초안을 작성합니다.
5. **법규 준수 확인 (Compliance Check)**: 과대 광고나 금지된 표현이 있는지 검사하고 필요 시 수정합니다.
6. **결과 전달**: 최종 메시지와 타겟 고객 리스트를 클라이언트에 반환합니다.

## 🚀 시작하기

### 사전 요구사항
- Python 3.11 이상
- Node.js 18 이상
- OpenAI API Key
- Supabase Project Credentials

### 1. 프로젝트 클론

```bash
git clone <repository-url>
cd blooming-v1
```

### 2. Backend 설정

```bash
cd backend
# 가상환경 생성 및 실행 (.env 설정 필요)
python -m venv venv
./venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Frontend 설정

```bash
cd frontend
npm install
npm run dev
```

### 4. RecSys 설정
```bash
cd RecSys
pip install -r requirements.txt
python recommendation_model_API.py
```


## 🔍 테스트 가이드

### API 테스트 (FastAPI)
Swagger UI (`http://localhost:8000/docs`)에서 `POST /api/message`를 직접 테스트할 수 있습니다.

### Frontend Flow 테스트
1. 브라우저에서 `http://localhost:5173` 접속
2. Persona Card 선택 -> "메시지 생성" 클릭
3. 결과 화면에서 "메시지(초안)" 확인 및 "타겟 식별(User IDs)" 리스트 확인



## 📚 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📁 프로젝트 구조

```
blooming-v1/
├── frontend/           # React + TypeScript + Vite
│   ├── src/features/   # 비즈니스 로직 (Persona, Dashboard)
│   └── src/components/ # 공통 UI
├── backend/            # Python + FastAPI + LangGraph
│   ├── actions/        # LangGraph Workflow Nodes
│   ├── services/       # External Services (Supabase, LLM)
│   └── main.py         # Entry Point
├── RecSys/             # Recommendation System (DL Model)
│   ├── recommendation_model_API.py
│   └── models.py
└── specs/              # 기획 및 설계 문서
```

## 📝 향후 계획

- [x] Supabase 데이터베이스 연동 (Customer CRM)
- [x] RecSys 추천 엔진 연동
- [x] 페르소나 기반 타겟팅 로직 구현
- [ ] 사용자 인증 및 권한 관리
- [ ] 메시지 히스토리 영구 저장 및 조회 대시보드
- [ ] A/B 테스트 기능 (메시지 효율 분석)
- [ ] 배포 자동화 (Docker, CI/CD)

## 📄 라이선스

MIT License

## 👥 기여자

- 개발자: [Your Name]

