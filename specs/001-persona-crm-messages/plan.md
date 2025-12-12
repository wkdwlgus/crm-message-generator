# Implementation Plan: Persona-Based Hyper-Personalized CRM Message Generation System

**Branch**: `001-persona-crm-messages` | **Date**: 2025-12-12 | **Spec**: [spec.md](./spec.md)

## Summary

페르소나 기반 초개인화 CRM 메시지 자동 생성 시스템 개발. 고객 페르소나 특성과 개인 데이터를 결합하여 브랜드별 톤앤매너가 반영된 한국어 마케팅 메시지를 자동 생성합니다. LangGraph 기반 AI 에이전트 오케스트레이션을 통해 전략 수립, 상품 추천, 메시지 생성, 컴플라이언스 검증을 수행하며, 멀티채널(이메일, SMS, 푸시, 카카오톡) 최적화를 지원합니다.

## Technical Context

**Language/Version**: 
- Backend: Python 3.11+
- Frontend: TypeScript 5.x + React 18

**Primary Dependencies**: 
- Backend: FastAPI, LangGraph, OpenAI GPT-5 API, Supabase Python Client, Pydantic, python-dotenv
- Frontend: Vite, React, TypeScript, Tailwind CSS

**Storage**: Supabase (PostgreSQL 기반) - 고객 프로필, 페르소나, 상품 정보, 브랜드 톤앤매너, 메시지 히스토리

**Testing**: 
- Backend: pytest, pytest-asyncio, httpx (FastAPI 테스트)
- Frontend: Vitest, React Testing Library

**Target Platform**: 
- Backend: Linux 서버 (컨테이너 배포 가능)
- Frontend: 웹 브라우저 (모던 브라우저 지원)

**Project Type**: Web application (frontend + backend 분리)

**Performance Goals**: 
- 메시지 생성 응답 시간 < 30초 (P95)
- 동시 100 요청 처리 가능
- GPT-5 API 호출 최적화 (불필요한 재시도 최소화)

**Constraints**: 
- GPT-5 API 응답 시간에 종속적
- 컴플라이언스 검증 실패 시 최대 5회 재시도
- 한국어 전용 (다국어 확장성 고려 불필요)
- 화장품법 준수 필수

**Scale/Scope**: 
- 초기 타겟: 아모레퍼시픽 자회사 브랜드 (Sulwhasoo, Hera 등)
- 페르소나: 10-20개 사전 정의
- 고객: 수만 명 규모 처리 가능해야 함
- 상품 카탈로그: 수천 개 SKU

## Constitution Check

*GATE: Constitution 파일이 템플릿 상태이므로 기본 개발 원칙 적용*

### 기본 개발 원칙 준수 확인

✅ **모듈화**: LangGraph 노드를 독립적인 모듈로 분리 (orchestrator, info_retrieval, message_writer, compliance_check, return_response)  
✅ **테스트 가능성**: 각 노드별 단위 테스트 가능한 구조  
✅ **명확한 인터페이스**: Pydantic 스키마로 데이터 검증 및 타입 안전성 확보  
✅ **관심사 분리**: Frontend (UI/UX) ↔ Backend (비즈니스 로직) 명확히 분리  
✅ **확장 가능성**: 새로운 브랜드/페르소나/채널 추가 용이한 구조

### 복잡도 평가

- **적정**: LangGraph를 사용한 워크플로우 오케스트레이션은 복잡한 AI 에이전트 로직 관리에 적합
- **적정**: Supabase 사용으로 인프라 복잡도 최소화
- **주의**: GPT-5 의존성으로 인한 외부 서비스 장애 대응 필요

## Project Structure

### Documentation (this feature)

```
specs/001-persona-crm-messages/
├── spec.md                    # 기능 명세서 (완료)
├── plan.md                    # 이 파일 - 구현 계획
├── research.md                # Phase 0: 기술 조사 결과
├── data-model.md              # Phase 1: 데이터 모델 설계
├── quickstart.md              # Phase 1: 빠른 시작 가이드
├── contracts/                 # Phase 1: API 계약
│   ├── openapi.yaml          # REST API 명세
│   └── schemas/              # 데이터 스키마
└── checklists/
    └── requirements.md        # 품질 체크리스트 (완료)
```

### Source Code (repository root)

```
blooming-v1/
├── backend/
│   ├── actions/                    # LangGraph 노드 모듈
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # 전략 수립 노드
│   │   ├── info_retrieval.py      # 정보 추출 노드
│   │   ├── message_writer.py      # 메시지 생성 노드
│   │   ├── compliance_check.py    # 컴플라이언스 검증 노드
│   │   └── return_response.py     # 응답 반환 노드
│   │
│   ├── models/                     # Pydantic 데이터 모델
│   │   ├── __init__.py
│   │   ├── user.py                # Customer Profile 스키마
│   │   ├── product.py             # Product 스키마
│   │   ├── persona.py             # Persona 스키마
│   │   ├── brand.py               # Brand Profile 스키마
│   │   ├── message.py             # Generated Message 스키마
│   │   ├── channel.py             # Channel Configuration 스키마
│   │   └── compliance.py          # Compliance Rule 스키마
│   │
│   ├── services/                   # 비즈니스 로직 서비스
│   │   ├── __init__.py
│   │   ├── supabase_client.py    # Supabase 연결 및 쿼리
│   │   ├── openai_client.py      # OpenAI GPT-5 API 클라이언트
│   │   └── message_service.py    # 메시지 생성 오케스트레이션
│   │
│   ├── api/                        # FastAPI 라우터
│   │   ├── __init__.py
│   │   └── message.py            # GET /message 엔드포인트
│   │
│   ├── config.py                   # 환경 변수 및 설정
│   ├── graph.py                    # LangGraph 워크플로우 정의
│   ├── main.py                     # FastAPI 앱 엔트리포인트
│   ├── requirements.txt            # Python 의존성
│   └── README.md
│
├── frontend/                       # Vite + React + TypeScript (구성 완료)
│   ├── src/
│   │   ├── components/            # React 컴포넌트
│   │   │   ├── MessageGenerator.tsx
│   │   │   ├── PersonaSelector.tsx
│   │   │   ├── CustomerSearch.tsx
│   │   │   ├── MessagePreview.tsx
│   │   │   └── ChannelSelector.tsx
│   │   │
│   │   ├── services/              # API 통신 레이어
│   │   │   └── messageApi.ts
│   │   │
│   │   ├── types/                 # TypeScript 타입 정의
│   │   │   ├── persona.ts
│   │   │   ├── customer.ts
│   │   │   ├── product.ts
│   │   │   └── message.ts
│   │   │
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   │
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── README.md
│
├── tests/
│   ├── backend/
│   │   ├── unit/                  # 단위 테스트
│   │   │   ├── test_orchestrator.py
│   │   │   ├── test_info_retrieval.py
│   │   │   ├── test_message_writer.py
│   │   │   └── test_compliance_check.py
│   │   │
│   │   ├── integration/           # 통합 테스트
│   │   │   ├── test_graph_flow.py
│   │   │   └── test_api_endpoints.py
│   │   │
│   │   └── fixtures/              # 테스트 데이터
│   │       ├── mock_users.json
│   │       └── mock_products.json
│   │
│   └── frontend/
│       └── (Vitest 설정 예정)
│
├── .env                            # 환경 변수 (gitignore)
├── .env.example                    # 환경 변수 템플릿
├── .gitignore
└── README.md
```

**Structure Decision**: Web application 구조 선택 (frontend + backend 분리). 이미 frontend와 backend 디렉토리가 존재하므로 해당 구조 활용. LangGraph 노드는 `backend/actions/`에 독립 모듈로 배치하여 테스트 및 유지보수 용이성 확보.

## Complexity Tracking

> Constitution이 템플릿 상태이므로 명시적 위반 사항 없음. 합리적인 아키텍처 선택으로 평가됨.

| 결정 사항 | 선택 이유 | 대안 및 기각 이유 |
|-----------|------------|-------------------------------------|
| LangGraph 사용 | AI 에이전트 워크플로우 오케스트레이션에 최적화된 프레임워크. 노드 간 상태 관리, 조건부 라우팅, 재시도 로직 구현 용이 | 직접 구현 시 복잡도 증가, LangChain만으로는 복잡한 플로우 관리 어려움 |
| Supabase 사용 | PostgreSQL 기반으로 관계형 데이터 모델 지원. BaaS로 인프라 관리 부담 최소화. Real-time 기능 향후 활용 가능 | 직접 PostgreSQL 설치는 운영 부담 증가, NoSQL은 관계형 데이터 모델 표현 제약 |
| FastAPI 사용 | 비동기 지원, 자동 문서화, Pydantic 통합으로 타입 안전성 확보 | Flask는 비동기 지원 약함, Django는 과도한 기능 (ORM 불필요) |
| Pydantic 스키마 | 런타임 데이터 검증 및 타입 안전성. OpenAPI 스키마 자동 생성 | TypeScript 스타일 타입 힌트만으로는 런타임 검증 불가 |


---

## Phase 0: Research (완료 )

### 생성된 문서
- **research.md**: 기술 스택 선정, 아키텍처 설계, 베스트 프랙티스 조사

### 주요 결정사항
1. LangGraph 5-노드 워크플로우 확정
2. GPT-5 API 프롬프트 엔지니어링 전략 수립
3. Supabase 데이터베이스 스키마 설계
4. 채널별 메시지 최적화 방법 정의
5. 컴플라이언스 검증 로직 설계
6. 환경 변수 관리 방법 확정
7. 프론트엔드 컴포넌트 구조 설계
8. 테스팅 전략 수립

---

## Phase 1: Design & Contracts (완료 )

### 생성된 문서
- **data-model.md**: 7개 핵심 엔티티 정의 (Pydantic 스키마 + DB 매핑)
  - Customer Profile
  - Persona
  - Product
  - Brand Profile
  - Generated Message
  - Channel Configuration
  - Compliance Rule

- **contracts/openapi.yaml**: REST API 명세 (OpenAPI 3.0)
  - GET /message 엔드포인트
  - 요청/응답 스키마
  - 에러 응답 정의

- **quickstart.md**: 개발 환경 설정 가이드
  - 의존성 설치 방법
  - 환경 변수 설정
  - Backend/Frontend 실행 방법
  - 문제 해결 가이드

### Agent Context 업데이트
- **GitHub Copilot**: 프로젝트 기술 스택 및 데이터베이스 정보 추가

---

## 구현 준비 완료

###  Phase 0 & Phase 1 완료 사항
- [x] 기술 조사 및 아키텍처 설계
- [x] 데이터 모델 정의 (7개 엔티티)
- [x] API 계약 명세 (OpenAPI)
- [x] 개발 환경 설정 가이드
- [x] Agent 컨텍스트 업데이트

###  다음 단계: 구현 시작

이제 다음 작업을 진행할 수 있습니다:

1. **Backend 구현**
   `ash
   # Pydantic 모델 생성 (backend/models/)
   # LangGraph 노드 구현 (backend/actions/)
   # FastAPI 엔드포인트 구현 (backend/api/)
   # Supabase 연결 서비스 구현 (backend/services/)
   `

2. **Frontend 구현**
   `ash
   # React 컴포넌트 생성 (frontend/src/components/)
   # API 통신 레이어 구현 (frontend/src/services/)
   # TypeScript 타입 정의 (frontend/src/types/)
   `

3. **테스트 작성**
   `ash
   # 단위 테스트 (tests/backend/unit/)
   # 통합 테스트 (tests/backend/integration/)
   `

###  참고 문서

모든 구현 세부사항은 다음 문서에서 확인할 수 있습니다:

- [spec.md](./spec.md) - 비즈니스 요구사항 (WHAT & WHY)
- [research.md](./research.md) - 기술 조사 및 설계 결정 (HOW)
- [data-model.md](./data-model.md) - 데이터 구조 및 스키마
- [contracts/openapi.yaml](./contracts/openapi.yaml) - API 명세
- [quickstart.md](./quickstart.md) - 개발 환경 설정

###  시작 명령어

`ash
# Backend 시작
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend 시작 (새 터미널)
cd frontend
npm install
npm run dev
`

---

**구현 계획 완료일**: 2025-12-12  
**다음 명령어**: 실제 코드 구현 시작 또는 /speckit.tasks로 작업 분해
