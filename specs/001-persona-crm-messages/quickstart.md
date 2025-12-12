# Quickstart Guide: Blooming CRM Message Generation

**Feature**: 001-persona-crm-messages | **Updated**: 2025-12-12

## 개요

이 가이드는 Blooming CRM 메시지 생성 시스템을 로컬 환경에서 빠르게 실행하는 방법을 설명합니다.

**예상 소요 시간**: 15-20분

---

## 사전 요구사항

### 필수 소프트웨어
- Python 3.11 이상
- Node.js 18 이상 + npm
- Git

### 필수 계정 및 API 키
- OpenAI API Key (GPT-5 접근 권한)
- Supabase 프로젝트 (URL + Anon Key)

---

## Step 1: 저장소 클론 및 브랜치 전환

```bash
# 저장소 클론 (이미 클론한 경우 스킵)
git clone <repository-url>
cd blooming-v1

# 피처 브랜치로 전환
git checkout 001-persona-crm-messages
```

---

## Step 2: 환경 변수 설정

### 2.1 `.env` 파일 생성

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력합니다:

```bash
# OpenAI API
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4  # GPT-5 사용 가능 시 변경

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# Application Settings
MAX_RETRY_COUNT=5
ENV=development

# CORS (Frontend 연동)
ALLOWED_ORIGINS=http://localhost:5173
```

### 2.2 환경 변수 확인

```bash
# .env.example 파일이 있다면 참고
cat .env.example
```

---

## Step 3: Backend 설정 및 실행

### 3.1 Python 가상 환경 생성

```bash
cd backend

# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3.2 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt** 예시:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
openai==1.3.0
supabase==2.0.0
langgraph==0.0.26
httpx==0.25.0
pytest==7.4.3
pytest-asyncio==0.21.1
```

### 3.3 Supabase 데이터베이스 초기화

Supabase Dashboard에서 SQL Editor를 열고 다음 스크립트를 실행합니다:

```sql
-- customers 테이블 생성
CREATE TABLE customers (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age_group VARCHAR(10) NOT NULL,
    gender CHAR(1),
    membership_level VARCHAR(20),
    skin_type TEXT[],
    skin_concerns TEXT[],
    preferred_tone VARCHAR(50),
    keywords TEXT[],
    acquisition_channel VARCHAR(100),
    average_order_value INTEGER,
    average_repurchase_cycle_days INTEGER,
    repurchase_cycle_alert BOOLEAN DEFAULT FALSE,
    shopping_behavior JSONB,
    coupon_profile JSONB,
    last_engagement JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Mock 데이터 삽입
INSERT INTO customers (user_id, name, age_group, gender, membership_level, skin_type, skin_concerns, keywords, repurchase_cycle_alert)
VALUES ('user_12345', '김아모레', '30s', 'F', 'VVIP', ARRAY['Dry', 'Sensitive'], ARRAY['Wrinkle', 'Dullness'], ARRAY['Vegan', 'Anti-aging'], TRUE);

-- products, brands, personas 테이블도 동일하게 생성 (data-model.md 참고)
```

### 3.4 Backend 서버 실행

```bash
# backend/ 디렉토리에서 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**출력 예시**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx]
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3.5 API 테스트

```bash
# 새 터미널에서 실행
curl -X GET "http://localhost:8000/message" \
  -H "x-user-id: user_12345"
```

**예상 응답**:
```json
{
  "message": "김아모레 고객님, VVIP 회원님만을 위한 특별한 소식...",
  "user": "user_12345",
  "method": "email"
}
```

---

## Step 4: Frontend 설정 및 실행

### 4.1 의존성 설치

```bash
cd frontend

npm install
```

### 4.2 Frontend 개발 서버 실행

```bash
npm run dev
```

**출력 예시**:
```
VITE v5.0.0  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### 4.3 브라우저에서 확인

브라우저에서 `http://localhost:5173`을 열어 UI를 확인합니다.

---

## Step 5: 전체 플로우 테스트

### 5.1 UI에서 메시지 생성 테스트

1. Customer ID 입력: `user_12345`
2. Persona 선택: (드롭다운에서 선택)
3. Channel 선택: `email`
4. **Generate Message** 버튼 클릭
5. 생성된 메시지 확인

### 5.2 다양한 시나리오 테스트

#### 시나리오 1: 존재하지 않는 고객
```bash
curl -X GET "http://localhost:8000/message" \
  -H "x-user-id: user_99999"
```

**예상 응답**: `404 User not found`

#### 시나리오 2: 헤더 누락
```bash
curl -X GET "http://localhost:8000/message"
```

**예상 응답**: `400 x-user-id header is required`

---

## 프로젝트 구조 확인

```bash
blooming-v1/
├── backend/
│   ├── actions/              # LangGraph 노드
│   ├── models/               # Pydantic 스키마
│   ├── services/             # 비즈니스 로직
│   ├── api/                  # FastAPI 라우터
│   ├── config.py
│   ├── graph.py
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
│
├── specs/001-persona-crm-messages/
│   ├── spec.md               # 기능 명세서
│   ├── plan.md               # 구현 계획
│   ├── research.md           # 기술 조사
│   ├── data-model.md         # 데이터 모델
│   ├── quickstart.md         # 이 파일
│   └── contracts/
│       └── openapi.yaml      # API 명세
│
└── .env                      # 환경 변수
```

---

## 자주 발생하는 문제 해결

### 문제 1: OpenAI API 오류
```
openai.error.RateLimitError: Rate limit exceeded
```

**해결책**:
- OpenAI API 할당량 확인
- `MAX_RETRY_COUNT`를 줄여서 재시도 횟수 감소
- API Key 권한 확인

### 문제 2: Supabase 연결 실패
```
ConnectionError: Failed to connect to Supabase
```

**해결책**:
- `.env` 파일의 `SUPABASE_URL` 및 `SUPABASE_KEY` 확인
- Supabase 프로젝트가 활성 상태인지 확인
- 네트워크 방화벽 설정 확인

### 문제 3: CORS 오류 (Frontend → Backend)
```
Access to fetch at 'http://localhost:8000/message' from origin 'http://localhost:5173' has been blocked by CORS policy
```

**해결책**:
- `backend/main.py`에서 CORS 미들웨어 설정 확인:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 문제 4: 컴플라이언스 검증 반복 실패
```
Failed to generate compliant message after 5 retries
```

**해결책**:
- GPT-5 프롬프트에 금칙어 리스트를 명확히 명시
- `backend/actions/compliance_check.py`의 금칙어 리스트 확인
- 임시로 컴플라이언스 검사 비활성화 (개발 단계에서만)

---

## 다음 단계

### Phase 1 완료 체크리스트
- [ ] Backend 서버 정상 실행
- [ ] Frontend 개발 서버 실행
- [ ] API 엔드포인트 테스트 성공
- [ ] Mock 데이터로 메시지 생성 테스트
- [ ] 컴플라이언스 검증 동작 확인

### Phase 2로 진행
- 실제 추천 알고리즘 개발
- 톤앤매너 few-shot 프롬프트 삽입
- 프로덕션 배포 준비
- 모니터링 및 로깅 강화

---

## 추가 리소스

- **API 문서**: http://localhost:8000/docs (FastAPI 자동 생성)
- **데이터 모델**: [data-model.md](./data-model.md)
- **기술 조사**: [research.md](./research.md)
- **전체 계획**: [plan.md](./plan.md)

---

## 지원

문제가 발생하면 다음을 확인하세요:
1. `.env` 파일의 모든 필수 변수가 설정되었는지
2. Python 및 Node.js 버전이 요구사항을 충족하는지
3. 모든 의존성이 올바르게 설치되었는지
4. Supabase 데이터베이스에 Mock 데이터가 존재하는지

추가 도움이 필요하면 팀에 문의하세요.
