# Research Document: Persona-Based CRM Message Generation

**Feature**: 001-persona-crm-messages | **Date**: 2025-12-12  
**Purpose**: Phase 0 기술 조사 - 핵심 의사결정 및 베스트 프랙티스 도출

## 1. LangGraph 아키텍처 설계

### 결정사항
**선택**: LangGraph를 사용한 5-노드 워크플로우 구조 채택

### 근거
- **복잡한 AI 워크플로우 관리**: 조건부 라우팅, 상태 관리, 재시도 로직을 선언적으로 표현 가능
- **디버깅 용이성**: 각 노드의 입출력을 명확히 추적 가능
- **테스트 가능성**: 노드 단위 독립 테스트 가능

### 노드 설계

#### Node 1: Orchestrator (전략 수립)
- **Input**: Customer Profile (User 데이터)
- **Output**: Message Strategy (타겟 페르소나, 메시지 방향성, 캠페인 유형)
- **책임**: 고객 데이터 분석 → 최적 메시지 전략 결정
- **구현 고려사항**:
  - 재구매 주기 도래 여부 확인 (`repurchase_cycle_alert`)
  - 장바구니 이탈 상품 존재 여부
  - 최근 조회 상품과 구매 이력의 관련성 분석

#### Node 2: Info Retrieval (정보 추출)
- **Input**: Message Strategy
- **Output**: Product Info + Brand Tone & Manner
- **책임**: 
  - Supabase에서 추천 상품 조회 (Phase 1에서는 Mock 데이터)
  - 해당 브랜드의 톤앤매너 템플릿 로드
- **구현 고려사항**:
  - 톤앤매너는 few-shot 프롬프트 형태로 저장 (예시 메시지 3-5개)
  - 상품 추천 로직은 별도 함수로 분리하여 향후 ML 모델 통합 용이하게

#### Node 3: Message Writer (메시지 생성)
- **Input**: Customer Profile + Product Info + Brand Tone + Message Strategy
- **Output**: Generated Message (초안)
- **책임**: GPT-5 API 호출하여 최종 메시지 생성
- **구현 고려사항**:
  - 시스템 프롬프트에 브랜드 톤앤매너 주입
  - 유저 프롬프트에 고객 데이터 및 상품 정보 구조화하여 전달
  - Temperature 설정: 0.7 (창의성과 일관성 균형)
  - Max tokens: 채널별 차등 (SMS: 200, 이메일: 800)

#### Node 4: Compliance Check (컴플라이언스 검증)
- **Input**: Generated Message
- **Output**: `compliance_passed` (bool) + `retry_count` (int)
- **책임**: 화장품법 금칙어 검사
- **구현 고려사항**:
  - 금칙어 리스트: DB 또는 config 파일로 관리
  - 실패 시 fallback → Message Writer (최대 5회)
  - 재시도 시 프롬프트에 "이전에 검출된 금칙어: [...]" 추가

#### Node 5: Return Response (응답 반환)
- **Input**: Validated Message + Metadata
- **Output**: API Response
- **책임**: 최종 응답 포맷팅 및 메타데이터 추가

### 상태 관리 (GraphState)
```python
class GraphState(TypedDict):
    user_data: Dict  # Customer Profile
    strategy: Dict  # Orchestrator 출력
    product: Dict  # 추천 상품
    brand_tone: str  # 톤앤매너 프롬프트
    message: str  # 생성된 메시지
    compliance_passed: bool
    retry_count: int
    channel: str  # email | sms | app_push | kakaotalk
```

### 대안 검토
- **LangChain 단독 사용**: 복잡한 조건부 플로우 표현 어려움 → 기각
- **직접 구현 (순수 Python)**: 상태 관리, 재시도 로직 직접 구현 필요 → 개발 시간 증가 → 기각

---

## 2. GPT-5 API 통합 전략

### 결정사항
**선택**: OpenAI GPT-5 API를 직접 호출 (openai Python SDK 사용)

### 프롬프트 엔지니어링 전략

#### 시스템 프롬프트 구조
```
당신은 [브랜드명]의 CRM 마케팅 메시지 작성 전문가입니다.

[브랜드 톤앤매너]
- 예시 메시지 1: ...
- 예시 메시지 2: ...
- 예시 메시지 3: ...

[주의사항]
- 화장품법 준수: "완치", "최고", "기적" 등 금칙어 사용 금지
- 한국어로만 작성
- [채널명] 형식에 맞춤: [글자 수 제한 등]
```

#### 유저 프롬프트 구조
```
[고객 정보]
- 이름: {name}
- 나이대: {age_group}
- 멤버십: {membership_level}
- 피부타입: {skin_type}
- 관심 키워드: {keywords}

[추천 상품]
- 상품명: {product_name}
- 가격: {original_price} → {discounted_price} (할인율: {discount_rate}%)
- 리뷰 키워드: {top_keywords}

[메시지 목적]
{strategy_description}

위 정보를 바탕으로 고객에게 발송할 CRM 메시지를 작성해주세요.
```

### API 호출 최적화
- **타임아웃 설정**: 25초 (전체 응답 시간 30초 목표)
- **재시도 전략**: Compliance 실패 시만 재시도 (네트워크 실패는 에러 반환)
- **스트리밍**: Phase 1에서는 미지원, Phase 2에서 검토

### 대안 검토
- **다른 LLM (Claude, Gemini)**: GPT-5가 한국어 성능 우수하다고 판단 → 현 시점에서 OpenAI 선택
- **자체 LLM fine-tuning**: 초기 비용 및 유지보수 부담 → 기각

---

## 3. Supabase 데이터베이스 설계

### 결정사항
**선택**: Supabase (PostgreSQL) 사용, 정규화된 관계형 모델 설계

### 테이블 구조

#### `customers` 테이블
```sql
CREATE TABLE customers (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    age_group VARCHAR(10),  -- '20s', '30s', '40s', '50s+'
    gender CHAR(1),
    membership_level VARCHAR(20),
    skin_type TEXT[],  -- PostgreSQL array
    skin_concerns TEXT[],
    preferred_tone VARCHAR(50),
    keywords TEXT[],
    acquisition_channel VARCHAR(100),
    average_order_value INTEGER,
    average_repurchase_cycle_days INTEGER,
    repurchase_cycle_alert BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `personas` 테이블
```sql
CREATE TABLE personas (
    persona_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    age_range VARCHAR(20),
    income_level VARCHAR(50),
    communication_tone VARCHAR(50),  -- 'formal', 'casual', 'friendly'
    detail_level VARCHAR(50),  -- 'brief', 'comprehensive'
    interests TEXT[],
    pain_points TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `products` 테이블
```sql
CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    brand VARCHAR(100),
    name VARCHAR(200),
    category_major VARCHAR(100),
    category_middle VARCHAR(100),
    category_small VARCHAR(100),
    original_price INTEGER,
    discounted_price INTEGER,
    discount_rate INTEGER,
    review_score DECIMAL(2,1),
    review_count INTEGER,
    top_keywords TEXT[],
    description_short TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `brands` 테이블
```sql
CREATE TABLE brands (
    brand_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(100) UNIQUE NOT NULL,
    target_demographic VARCHAR(200),
    tone_manner_style VARCHAR(50),  -- 'sophisticated', 'youthful', 'luxury'
    tone_manner_examples TEXT,  -- JSON 또는 구분자로 저장된 예시 메시지들
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `generated_messages` 테이블 (메시지 히스토리)
```sql
CREATE TABLE generated_messages (
    message_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES customers(user_id),
    persona_used VARCHAR(100),
    product_id VARCHAR(50) REFERENCES products(product_id),
    brand_name VARCHAR(100),
    channel VARCHAR(50),
    message_text TEXT,
    compliance_passed BOOLEAN,
    retry_count INTEGER,
    generated_at TIMESTAMP DEFAULT NOW()
);
```

### 인덱싱 전략
```sql
CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_generated_messages_user_id ON generated_messages(user_id);
CREATE INDEX idx_generated_messages_generated_at ON generated_messages(generated_at DESC);
```

### Mock 데이터 전략
- Phase 1에서는 customers, products, brands 테이블에 샘플 데이터 10-20건 삽입
- Supabase UI 또는 SQL 스크립트로 초기 데이터 로드

### 대안 검토
- **NoSQL (MongoDB, DynamoDB)**: 관계형 데이터 모델 표현 제약, JOIN 어려움 → 기각
- **직접 PostgreSQL 설치**: 운영 및 백업 부담 → Supabase로 BaaS 활용 선택

---

## 4. 채널별 메시지 최적화 전략

### 결정사항
**선택**: 채널별 특성에 따른 프롬프트 및 검증 규칙 차별화

### 채널 규격

| 채널 | 최대 길이 | 형식 | 특징 |
|------|-----------|------|------|
| SMS | 160자 (한글 기준 70자) | 플레인 텍스트 | 링크 1개 포함 필수 |
| 이메일 | 제목 50자 + 본문 800자 | HTML 가능 | 이미지, 버튼 포함 가능 |
| 앱 푸시 | 제목 30자 + 본문 100자 | 플레인 텍스트 | 즉각적 주목 필요 |
| 카카오톡 | 1000자 | 텍스트 + 버튼 | 이미지 첨부 가능 |

### 채널별 프롬프트 수정
- GPT-5 프롬프트에 채널 제약조건 명시
  - 예: "SMS용 메시지입니다. 70자 이내로 작성하고, 상품 페이지 링크를 포함하세요."

### 검증 로직
```python
def validate_channel_constraints(message: str, channel: str) -> bool:
    constraints = {
        'sms': 70,
        'email': 800,
        'app_push': 100,
        'kakaotalk': 1000
    }
    return len(message) <= constraints.get(channel, 1000)
```

### 대안 검토
- **단일 메시지 생성 후 잘라내기**: 맥락 손실 우려 → 채널별 최적 생성 선택

---

## 5. 컴플라이언스 검증 구현

### 결정사항
**선택**: 키워드 기반 금칙어 검사 + 재시도 로직

### 금칙어 리스트 예시
```python
PROHIBITED_WORDS = [
    "완치", "치료", "의약", "의학", "임상",
    "최고", "세계 최초", "1등", "독보적",
    "기적", "마법", "신기", "놀라운",
    "100%", "절대", "전혀", "무조건",
    "살이 빠지는", "체지방 감소", "다이어트",
    "부작용 없음", "안전성 입증"
]
```

### 검증 로직
```python
def check_compliance(message: str) -> Tuple[bool, List[str]]:
    """금칙어 검사. (통과 여부, 검출된 금칙어 리스트) 반환"""
    found_words = [word for word in PROHIBITED_WORDS if word in message]
    return (len(found_words) == 0, found_words)
```

### 재시도 전략
- 최대 5회 재시도
- 재시도 시 프롬프트에 추가: "다음 단어들은 사용하지 마세요: {found_words}"
- 5회 초과 시 에러 응답 반환 (프론트엔드에서 수동 수정 유도)

### Phase 2 개선 방향
- LLM 기반 의미 분석 (금칙어 우회 표현 탐지)
- 정규표현식 패턴 매칭 강화

### 대안 검토
- **외부 컴플라이언스 API**: 비용 및 응답시간 증가 → Phase 1에서는 자체 구현

---

## 6. 환경 변수 및 보안 관리

### 결정사항
**선택**: `python-dotenv` + `.env` 파일 사용, `config.py`로 중앙 관리

### `.env` 파일 구조
```bash
# OpenAI API
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGci...

# Application Settings
MAX_RETRY_COUNT=5
ENV=development

# CORS (Frontend 연동)
ALLOWED_ORIGINS=http://localhost:5173
```

### `config.py` 구현
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-5"
    supabase_url: str
    supabase_key: str
    max_retry_count: int = 5
    env: str = "development"
    allowed_origins: str = "http://localhost:5173"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 보안 고려사항
- `.env` 파일은 `.gitignore`에 추가
- `.env.example` 제공 (값 없이 키만 명시)
- Production 환경에서는 환경 변수 또는 Secret Manager 사용

---

## 7. 프론트엔드 아키텍처

### 결정사항
**선택**: React + TypeScript + Tailwind CSS, 컴포넌트 기반 설계

### 핵심 컴포넌트

#### 1. MessageGenerator (메인 컴포넌트)
- 상태 관리: 페르소나, 고객, 채널 선택 상태
- 메시지 생성 API 호출
- 로딩/에러 처리

#### 2. PersonaSelector
- 페르소나 목록 표시
- 선택된 페르소나 하이라이트

#### 3. CustomerSearch
- 고객 ID 입력 (x-user-id)
- 자동완성 기능 (Phase 2)

#### 4. ChannelSelector
- 채널 선택 (라디오 버튼 또는 드롭다운)

#### 5. MessagePreview
- 생성된 메시지 표시
- 수동 편집 기능
- 복사 버튼

### API 통신 레이어
```typescript
// services/messageApi.ts
export interface MessageRequest {
  userId: string;
}

export interface MessageResponse {
  message: string;
  user: string;
  method: 'email' | 'sms' | 'app_push' | 'kakaotalk';
}

export async function generateMessage(
  userId: string
): Promise<MessageResponse> {
  const response = await fetch('/message', {
    method: 'GET',
    headers: {
      'x-user-id': userId
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to generate message');
  }
  
  return response.json();
}
```

### 상태 관리
- Phase 1: React `useState` + `useEffect` (단순)
- Phase 2: Zustand 또는 Context API (복잡도 증가 시)

---

## 8. 테스팅 전략

### 단위 테스트 (pytest)
- 각 LangGraph 노드 독립 테스트
- Pydantic 모델 검증 테스트
- 컴플라이언스 검사 로직 테스트

### 통합 테스트
- LangGraph 전체 플로우 E2E 테스트 (Mock GPT-5 API)
- FastAPI 엔드포인트 테스트 (httpx TestClient)

### 프론트엔드 테스트 (Vitest)
- 컴포넌트 렌더링 테스트
- API 호출 Mocking (MSW)

### 테스트 픽스처
- `tests/backend/fixtures/mock_users.json`
- `tests/backend/fixtures/mock_products.json`

---

## 9. 배포 및 운영 고려사항

### 개발 환경
- Backend: `uvicorn main:app --reload`
- Frontend: `npm run dev`

### 프로덕션 배포 (Phase 2)
- Backend: Docker 컨테이너화 + Cloud Run / ECS
- Frontend: Vercel / Netlify
- 환경 변수: Secret Manager 사용

### 모니터링
- 로깅: Python `logging` 모듈
- 메트릭: 메시지 생성 시간, 재시도 횟수, 실패율

---

## 요약 및 다음 단계

### 해결된 질문들
✅ LangGraph 5-노드 구조 확정  
✅ GPT-5 API 프롬프트 엔지니어링 전략 수립  
✅ Supabase 데이터베이스 스키마 설계  
✅ 채널별 메시지 최적화 방법 정의  
✅ 컴플라이언스 검증 로직 설계  
✅ 환경 변수 관리 방법 확정  
✅ 프론트엔드 컴포넌트 구조 설계  
✅ 테스팅 전략 수립

### Phase 1으로 진행
다음 단계에서는 `data-model.md`, `contracts/openapi.yaml`, `quickstart.md`를 생성하여 구체적인 구현 가이드를 제공합니다.
