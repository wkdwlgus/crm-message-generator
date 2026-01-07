
## msgbot_node.md

## 구조 설명

### 1. LangGraph 워크플로우 (CRM Message Generator)

이 시스템은 고객 데이터, 상품 정보, CRM 이력을 기반으로 개인화된 마케팅 메시지를 생성하는 **LangGraph 기반 파이프라인**입니다.

**Workflow Diagram:**

```mermaid
graph TD
    Start[Orchestrator] --> Info[Info Retrieval]
    Info --> Retrieve{Retrieve CRM (Cache)}
    
    Retrieve -- Hit --> Personalize[Personalize]
    Retrieve -- Miss --> Writer[Message Writer]
    
    Writer --> Compliance{Compliance Check}
    
    Compliance -- Pass --> Save[Save CRM]
    Compliance -- Fail (Retry) --> Writer
    Compliance -- Fail (Max Retries) --> Return[Return Response]
    
    Save --> Personalize
    Personalize --> Return
    Return --> End
```

### 2. Prompt Layer 분리 장점

- **톤 일관성**: 브랜드별 Static Rule(`crm_guideline.json`) 적용.
- **안정성**: Prompt와 Logic의 분리로 환각 최소화.
- **확장성**: 브랜드/채널 추가 시 코드 수정 없이 JSON/Config 수정만으로 대응.
- **비용 최적화**: Cache Hit 시 LLM 호출 0회.

---

## 파일 구조 및 역할

### 0. graph.py

- **역할**: 전체 노드를 연결하는 워크플로우 정의.
- **주요 로직**:
  - `GraphState` 정의 (`use_crm_cache` 플래그 추가).
  - `RetrieveCRM`에서의 캐시 분기 (`Hit` vs `Miss`).
  - `ComplianceCheck`에서의 재시도 루프 및 저장 분기.
  - `Personalize`로의 최종 흐름 통합.

### 1. actions/orchestrator.py

- **역할**: 초기 전략 수립 및 상태 초기화.
- **주요 로직**:
  - `crm_reason`(발송 의도) 및 `use_crm_cache`(재사용 여부) 초기화.
  - 고객 페르소나 및 추천 전략 결정.
- **Input**: User/Context Data
- **Output**: `state["strategy"]`, `state["recommended_brand"]`

### 2. actions/retrieve_crm.py (New)

- **역할**: 메시지 재사용을 위한 CRM 이력 검색 (Cache Check).
- **주요 로직**:
  - `use_crm_cache=True`일 때만 동작.
  - 상품, 의도, 채널, Persona, Beauty Profile(Strict) 일치 여부 확인.
- **Output**:
  - Hit: `state["cache_hit"]=True`, `state["message_template"]` 설정.
  - Miss: `state["cache_hit"]=False`, 다음 단계(`Writer`)로 진행.

### 3. actions/message_writer.py (Modified)

- **역할**: LLM 기반 신규 메시지 생성 (Template).
- **주요 로직**:
  - Prompt 구성: Sender(Brand) + Receiver(Persona) + Context(Intent) + Channel Rule.
  - `{{customer_name}}` 플레이스홀더를 사용하여 템플릿 형태로 생성.
  - **캐시/저장 로직 제거** (순수 생성 역할에 집중).
- **Output**: `state["message_template"]`

### 4. actions/compliance_check.py (Modified)

- **역할**: 화장품법 및 마케팅 규정 준수 여부 검사.
- **주요 로직**:
  - 생성된 메시지의 금지어/과장 광고 여부 판단 (LLM Judge).
  - **저장 로직 제거** (검수 역할에 집중).
- **Output**: `state["compliance_passed"]`, `state["error_reason"]`

### 5. actions/save_crm.py (New)

- **역할**: 검수 통과된 메시지의 DB 저장.
- **주요 로직**:
  - 검수 통과 시(`compliance_passed=True`) 실행.
  - `crm_history_service`를 호출하여 DB에 Insert (KST Timestamp).
  - 저장 대상: Template 메시지 (이름 치환 전).

### 6. actions/personalize.py (New)

- **역할**: 최종 메시지 개인화 (Post-processing).
- **주요 로직**:
  - 캐시된 템플릿 또는 신규 생성된 템플릿의 `{{customer_name}}`을 실제 고객 이름으로 치환.
  - 모든 경로(New/Reuse)의 최종 종착지.
- **Output**: `state["message"]` (최종 발송본)

### 7. services/crm_history_service.py

- **역할**: Supabase `crm_message_history` 테이블 핸들링.
- **특징**:
  - `_generate_signature`: 검색 조건의 Hash 생성 (Exact Match 보장).
  - `save_message`: `created_at`을 **KST(Asia/Seoul)** 기준으로 저장.

---

## 환경 변수 및 의존성

- `OPENAI_API_KEY`: GPT-4o 호출.
- `SUPABASE_URL`, `SUPABASE_KEY`: 고객/상품/이력 DB 접근.
- `USE_MOCK`: (Optional) 테스트용 Mock 데이터 사용 여부.

---

## 실행 가이드

1. **API 실행**: `python main.py` or `uvicorn main:app --reload`
2. **테스트**: `python backend/utils/verify_new_graph.py` (전체 흐름 검증)
