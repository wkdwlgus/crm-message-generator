# Blooming 제품 추천 시스템 (RecSys)

Cross-Encoder 기반 개인화 제품 추천 API

## 📋 개요

고객의 피부 타입, 고민, 선호 키워드를 분석하여 최적의 화장품을 추천하는 시스템입니다.
벡터 임베딩과 Cross-Encoder를 결합하여 높은 정확도의 추천을 제공합니다.

## 🎯 Intent 기반 추천 시나리오

### 1. Regular Intent (일반 추천)
**사용 시기**: 일반적인 개인화 추천

```json
{
  "user_id": "user_12345",
  "intention": "" // 또는 "regular"
}
```

**추천 로직**:
1. 고객 프로필 분석 (피부타입, 고민, 키워드)
2. 벡터 유사도 검색으로 후보 200개 추출
3. Cross-Encoder로 정밀 점수 계산
4. 유저 키워드 매칭 보너스 적용
5. **최종 점수(final_score) 기준 정렬**

**점수 계산**:
```
final_score = ce_score + (1.2 × keyword_bonus)
```

**예시**:
- 유저: "Vegan", "Anti-aging" 키워드
- 제품 A: ce=0.85, kw=0.6 → **final=1.57**
- 제품 B: ce=0.90, kw=0.3 → final=1.26

→ **제품 A 추천** (키워드 매칭이 더 좋음)

---

### 2. Event Intent (할인 행사)
**사용 시기**: 블랙프라이데이, 할인 프로모션, 쿠폰 발송

```json
{
  "user_id": "user_12345",
  "intention": "event"
}
```

**추천 로직**:
1. Regular와 동일하게 관련도 점수 계산
2. **final_score 기준으로 Top 5 추출**
3. **Top 5 중 할인율(discount_rate) 기준으로 재정렬**
4. 최종 1위 제품 선택

**정렬 기준**:
```python
# Step 1: final_score로 Top 5 선정
top_5 = sorted(products, key=lambda x: x['final_score'], reverse=True)[:5]

# Step 2: Top 5 중 할인율로 재정렬
top_5.sort(key=lambda x: x['discount_rate'], reverse=True)
```

**예시**:
```
전체 후보:
- 제품 A: final=1.80, 할인 4%
- 제품 B: final=1.71, 할인 10%
- 제품 C: final=1.57, 할인 15% ✅ **Top 5 진입**
- 제품 D: final=1.26, 할인 15%
- 제품 E: final=0.95, 할인 41% ❌ **Top 5 탈락**

Top 5 추출 후 할인율로 재정렬:
1. 제품 C: 할인 15%, final=1.57 ✅ **최종 선택**
2. 제품 D: 할인 15%, final=1.26
3. 제품 B: 할인 10%, final=1.71
...
```

→ **제품 C 추천** (고관련도 제품 중 최고 할인율)

**장점**:
- ✅ 유저 니즈와 무관한 저가 할인 제품 배제
- ✅ 관련도 높은 제품 중에서만 할인율 비교
- ✅ 추천 품질과 할인 혜택 균형

---

### 3. Weather Intent (날씨/시즌별)
**사용 시기**: 계절 변화, 날씨 기반 맞춤 추천

```json
{
  "user_id": "user_12345",
  "intention": "weather"
}
```

**추천 로직**:
1. **현재 날짜로 시즌 자동 판단** (1월=겨울, 7월=여름)
2. 시즌별 키워드를 유저 키워드에 추가
3. **시즌 핵심 키워드에 2배 가중치 부여** (Priority Keyword System)
4. 강화된 키워드 매칭으로 final_score 계산
5. 최종 점수 기준 정렬

**시즌별 키워드 (23-31개/계절)**:

#### 봄 (3-5월) - 총 23개 키워드
- **날씨 이슈**: 미세먼지, 황사, 꽃가루 알레르기
- **일반 키워드**: 진정, 보호막, 클렌징, 항산화, 순한 제형, 민감성, 진정효과
- **우선순위 키워드 (2배)**: 진정, 민감, 순한, 저자극, 보호, 배리어, 피부보호, 클렌징, 딥클렌징

#### 여름 (6-8월) - 총 31개 키워드
- **날씨 이슈**: 폭염, 자외선, 장마(습도), 땀, 피지
- **일반 키워드**: SPF, PA, 자외선차단, 유분조절, 피지, 모공, 쿨링, 가벼운 제형, 산뜻한
- **우선순위 키워드 (2배)**: 산뜻, 가벼운, 쿨링, SPF, PA, 자외선차단, 피지조절, 모공케어, 유분조절, 젤, 청량감

#### 가을 (9-11월) - 총 23개 키워드
- **날씨 이슈**: 큰 일교차, 건조한 대기, 환절기
- **일반 키워드**: 보습, 수분, 영양, 장벽 리페어, 세라마이드, 촉촉한, 밸런스
- **우선순위 키워드 (2배)**: 보습, 수분, 촉촉, 장벽, 배리어, 피부장벽, 장벽리페어, 세라마이드, 히알루론산

#### 겨울 (12-2월) - 총 24개 키워드
- **날씨 이슈**: 한파, 극건조
- **일반 키워드**: 고보습, 크림, 오일, 농축, 리치, 영양크림, 촉촉한보습감
- **우선순위 키워드 (2배)**: 보습, 고보습, 수분, 극건조, 건조, 크림, 리치, 농축, 밀착, 오일, 영양크림, 세라마이드, 피부장벽

**우선순위 키워드 시스템**:
```python
# 일반 키워드: +1.0 점수
# 우선순위 키워드: +2.0 점수 (2배 가중치)

# 예시: 겨울 시즌
매칭된 키워드:
- "보습" (우선순위) → +2.0
- "크림" (우선순위) → +2.0
- "세라마이드" (우선순위) → +2.0
- "탄력" (일반) → +1.0

가중치 합산: 7.0 (우선순위 3개×2 + 일반 1개×1)
최대 가능 점수: 39개×2 = 78.0
keyword_bonus: 7.0 / 78.0 = 0.090
```

**예시 (1월 = 겨울)**:
```python
# 유저 키워드: ["Moisture", "Non_Comedogenic"]
# + 겨울 키워드: ["건조", "보습", "고보습", "수분", "크림", ...]

제품: "아토베리어365 바디크림"
제품 키워드: "촉촉한 보습감", "고보습 바디크림", "피부장벽", "세라마이드"

매칭 분석:
- "보습" ✅ (우선순위 키워드, 2배)
- "고보습" ✅ (우선순위 키워드, 2배)
- "크림" ✅ (우선순위 키워드, 2배)
- "세라마이드" ✅ (우선순위 키워드, 2배)
- "피부장벽" ✅ (우선순위 키워드, 2배)

우선순위 키워드 9개 매칭 → 가중치 18점
ce_score: 0.071
keyword_bonus: 0.231 (높은 계절 적합도!)
final_score: 0.071 + (1.2 × 0.231) = 0.348
```

**Regular vs Weather 차별화**:
```
사용자 ID 2번 테스트 결과:

Regular Intent:
- 추천: 코스알엑스 "더 나이아신아마이드 15 세럼"
- 키워드 매칭: 20% (3/15개)
- 최종 점수: 0.530

Weather Intent (겨울):
- 추천: 에스트라 "아토베리어365 바디크림" ✅ 다른 제품!
- 키워드 매칭: 23.1% (우선순위 9개 ×2배)
- 최종 점수: 0.348
- 겨울 특화 키워드: 보습, 고보습, 크림, 세라마이드, 피부장벽

→ Weather Intent는 계절 니즈에 최적화된 제품 선택
```

---

## 🔧 기술 스택

### 핵심 기술
- **벡터 임베딩**: OpenAI `text-embedding-3-small` (1536차원)
- **Re-ranking**: Cross-Encoder `BAAI/bge-reranker-v2-m3`
- **벡터 DB**: Supabase + pgvector

### 추천 파이프라인
```
1. 유저 쿼리 생성 → 피부타입/고민/키워드 종합
2. 벡터 임베딩 → 1536차원 벡터 변환
3. 유사도 검색 → 200개 후보 추출
4. 브랜드 필터링 → 지정 브랜드만 선택 (옵션)
5. Cross-Encoder → 정밀 관련도 점수 계산
6. 키워드 보너스 → 키워드 매칭 가중치 추가
7. Intent별 정렬 → 최종 제품 선택
```

---

## 📊 점수 계산 상세

### Keyword Bonus 계산

#### 일반/Event Intent
```python
# 키워드 매칭 점수 (0~1)
hit_count = 매칭된_키워드_개수  # 각 키워드당 +1.0
score = hit_count / 전체_키워드_개수

# 예시:
유저 키워드: ["보습", "탄력", "미백"] (3개)
제품 키워드: "촉촉한 보습감, 탄력 케어"

매칭:
- "보습" → 발견 (+1.0)
- "탄력" → 발견 (+1.0)
- "미백" → 없음 (+0.0)

score = 2.0 / 3.0 = 0.667
```

#### Weather Intent (우선순위 가중치)
```python
# 시즌 핵심 키워드는 2배 가중치
hit_count = (일반_매칭 × 1.0) + (우선순위_매칭 × 2.0)
max_score = 전체_키워드_개수 × 2.0  # 모두 우선순위라고 가정
score = hit_count / max_score

# 예시 (겨울):
유저 + 날씨 키워드: 39개
- 우선순위: ["보습", "고보습", "크림", "세라마이드", ...] (19개)
- 일반: ["한파", "건조", "영양", "리프팅", ...] (20개)

제품 매칭:
- "보습" (우선순위) → +2.0
- "고보습" (우선순위) → +2.0
- "크림" (우선순위) → +2.0
- "세라마이드" (우선순위) → +2.0
- "피부장벽" (우선순위) → +2.0
- "건조" (일반) → +1.0
- "수분" (우선순위) → +2.0
- "오일" (우선순위) → +2.0
- "촉촉한보습감" (우선순위) → +2.0

hit_count = 1.0×1 + 2.0×8 = 17.0
max_score = 39 × 2.0 = 78.0
score = 17.0 / 78.0 = 0.218

✅ 우선순위 시스템으로 계절 적합도 강조!
```

### Final Score
```python
final_score = ce_score + (1.2 × keyword_bonus)

# KW_BONUS_ALPHA = 1.2
# 키워드 매칭에 20% 가중치 부여
```

---

## 🚀 API 사용법

### 엔드포인트
```
POST http://localhost:8001/recommend
```

### Request Body
```json
{
  "user_id": "user_12345",
  "user_data": {
    "user_id": "user_12345",
    "name": "홍길동",
    "skin_type": ["Dry", "Sensitive"],
    "skin_concerns": ["Wrinkle", "Dullness"],
    "keywords": ["Vegan", "Anti-aging"]
  },
  "target_brand": ["헤라", "설화수"],
  "intention": "weather"
}
```

### Response
```json
{
  "product_id": "66735",
  "product_name": "리쥬브네이팅 트리트먼트 엠디 크림 50ml",
  "score": 1.93,
  "reason": "Cross-Encoder 점수: 0.8500, 키워드 매칭: 0.900",
  "product_data": {
    "product_id": "66735",
    "brand": "에이피뷰티",
    "name": "리쥬브네이팅 트리트먼트 엠디 크림 50ml",
    "category": {
      "major": "스킨케어",
      "middle": null,
      "small": null
    },
    "price": {
      "original_price": 126720,
      "discounted_price": 126720,
      "discount_rate": 4
    },
    "review": {
      "score": 4.8,
      "count": 184,
      "top_keywords": []
    },
    "description_short": "리쥬브네이팅 트리트먼트 엠디 크림 50ml - 에이피뷰티"
  }
}
```

---

## 📦 설정

### 환경 변수 (.env)
```bash
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...
```

### 실행
```bash
cd RecSys
python main.py

# 또는
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

---

## 🧪 테스트

```bash
# 시나리오별 테스트 실행
python test_scenarios.py
```

테스트 시나리오:
- ✅ Regular: 일반 개인화 추천
- ✅ Event: 할인율 기반 추천
- ✅ Weather (겨울): 시즌별 추천
- ✅ Weather (여름): 시즌별 추천

---

## 📈 성능 지표

### 추천 품질
- **벡터 검색 Recall@30**: 후보군 충분성 보장
- **Cross-Encoder Precision**: 정밀한 관련도 평가
- **Keyword Matching**: 유저 의도 반영
  - Regular: 15-20% (일반 키워드 매칭)
  - Weather: 20-25% (우선순위 키워드 2배 가중치)
  - Event: 25-30% (할인 제품 중 고관련도)

### 추천 다양성
- **Regular vs Weather 차별화**: ✅ 성공
  - 동일 유저에게 서로 다른 제품 추천 (계절 니즈 반영)
  - 예: Regular → 세럼, Weather(겨울) → 크림
- **Event vs Regular 차별화**: ✅ 성공
  - Event는 Top 5 고관련도 제품 중 할인율 우선

### 처리 속도
- 벡터 검색: ~100ms
- Cross-Encoder Re-ranking (30개): ~800ms
- 총 응답 시간: ~1000ms (GPU 사용 시 ~500ms)

---

## 🔄 워크플로우 통합

### Backend 연동
```python
# backend/actions/info_retrieval.py
from config import settings
import httpx

def call_recsys_api(user_data, target_brand, intent):
    response = httpx.post(
        settings.RecSys_API_URL,  # "http://localhost:8001/recommend"
        json={
            "user_id": user_data.user_id,
            "user_data": user_data.model_dump(),
            "target_brand": [target_brand] if target_brand else [],
            "intention": intent
        },
        timeout=30.0
    )
    return response.json()
```

### GraphState Intent 설정
```python
# backend/graph.py
state = {
    "user_id": "user_12345",
    "intent": "weather",  # "", "regular", "event", "weather"
    "recommended_brand": "헤라",
    ...
}
```

---

## 📝 데이터베이스 스키마

### customers 테이블
```sql
- user_id (text)
- skin_type (text[])
- skin_concerns (text[])
- keywords (text[])
- preferred_tone (text)
```

### products 테이블
```sql
- id (int)
- brand (text)
- name (text)
- category_major (text)
- discount_rate (int)
- price_final (int)
- review_score (float)
- features (jsonb)
- keywords (jsonb)
```

### products_vector 테이블
```sql
- product_id (int, FK)
- content (text)  -- 제품 상세 텍스트
- embedding (vector(1536))  -- 임베딩 벡터
```

---

## 🎨 활용 사례

### 1. CRM 메시지 개인화
- 고객별 최적 제품 추천
- 브랜드별 맞춤 메시지 생성

### 2. 시즌 마케팅
- 날씨/계절에 맞는 제품 프로모션
- 자동화된 시즌별 큐레이션

### 3. 할인 이벤트 최적화
- 고객 관련도 높은 제품 중 할인율 우선
- ROI 극대화

---

## 🔮 향후 개선 사항

- [ ] A/B 테스트 프레임워크
- [ ] 실시간 피드백 학습
- [ ] 다양성 보장 알고리즘 (diversity)
- [ ] 협업 필터링 통합
- [ ] 제품 이미지 기반 추천

---

## 📞 문의

문제가 발생하거나 개선 제안이 있으시면 이슈를 등록해주세요.
