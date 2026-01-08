# Blooming CRM Backend

FastAPI와 LangGraph를 활용한 AI 마케팅 에이전트 서버입니다.

## 🏗️ 시스템 아키텍처

이 백엔드는 **LangGraph**를 사용하여 상태 기반(State-based) 워크플로우를 처리합니다.

### 📌 LangGraph 워크플로우

1. **Orchestrator (`orchestrator.py`)**
   - 클라이언트로부터 페르소나 정보를 수신합니다.
   - Supabase `customer_crm` 테이블에서 해당 페르소나 조건(성별, 나이대, 피부타입 등)에 맞는 **유사 고객군(User IDs)**을 검색합니다.
   - 대량의 데이터 처리를 위해 Random Offset 방식을 사용하여 효율적으로 샘플링합니다.

2. **Retrieve CRM / Info Retrieval (`retrieve_crm.py`, `info_retrieval.py`)**
   - 타겟 고객 중 대표 샘플의 상세 정보를 조회합니다.
   - RecSys API를 호출하여 고객에게 적합한 추천 제품 정보를 가져옵니다.

3. **Message Writer (`message_writer.py`)**
   - 수집된 고객 정보, 제품 정보, 마케팅 가이드라인을 LLM(GPT-4o)에 주입합니다.
   - 선택된 채널(문자, 카카오톡 등) 포맷에 맞춰 초안을 작성합니다.

4. **Compliance Check (`compliance_check.py`)**
   - 작성된 메시지가 화장품법 및 광고 가이드라인을 준수하는지, 금지어를 사용하지 않았는지 검사합니다.
   - 위반 사항이 있을 경우 자동 수정 또는 재생성을 요청합니다.

5. **Return Response (`return_response.py`)**
   - 최종 생성된 메시지와 함께 타겟팅된 **Similar User IDs** 목록을 API 응답으로 반환합니다.

## 🛠️ 설치 및 실행 방법

1. **가상환경 설정**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

2. **환경 변수 설정 (`.env`)**
   ```env
   OPENAI_API_KEY=sk-...
   SUPABASE_URL=...
   SUPABASE_KEY=...
   RecSys_API_URL=http://localhost:8001/recommend
   ```

3. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

4. **서버 실행**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

## 🔌 API 명세

### `POST /api/message`
페르소나 정보를 받아 마케팅 메시지와 타겟 유저 목록을 생성합니다.

**Request:**
```json
{
  "persona": "30대 건성 여성",
  "gender": "Female",
  "age_group": "30s",
  "skin_type": "Dry",
  "worry": ["Wrinkles", "Hydration"],
  "tone_manner": "Polite",
  "channel": "kakaotalk"
}
```

**Response:**
```json
{
  "message": "안녕하세요! 건조한 피부...",
  "reasoning": "30대 건성 피부 고객을 위해...",
  "similar_user_ids": [101, 405, 230, ...]
}
```
