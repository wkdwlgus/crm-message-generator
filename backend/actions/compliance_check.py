"""
Compliance Check Node (RAG + LLM)
화장품법 준수 여부 검증

아키텍처:
1. Rule DB에서 관련 규칙 검색 (Vector Similarity + Keyword Matching)
2. 검색된 규칙과 제품 정보를 OpenAI API에 전달
3. LLM이 규칙 위반 여부 판단
4. 위반 시 최대 5회 재시도

State 해결 방법:
- GraphState에 필요한 필드 추가 (violated_rules, llm_reasoning, confidence_score)
- compliance_check_node 내부에서 product_data를 product_info/legal_info로 변환 (로컬 변수)
- 다른 노드와 공유하지 않는 필드는 로컬 변수로만 사용
"""
from typing import TypedDict, List, Dict, Any
from models.user import CustomerProfile
from openai import OpenAI
from supabase import create_client, Client
import os
import json
from dotenv import load_dotenv
from config import settings

# ===== GraphState 정의 (다른 노드와 공유) =====
class GraphState(TypedDict):
    """LangGraph State 정의"""
    user_id: str
    user_data: CustomerProfile
    recommended_brand: List[str]
    recommended_product_id: str
    product_data: dict
    brand_tone: dict
    channel: str
    message: str
    compliance_passed: bool
    retry_count: int
    error: str
    error_reason: str  # Compliance 실패 이유 (다른 노드와 공유)
    success: bool  # API 응답용
    # Compliance 전용 필드 (다른 노드와 공유하지 않지만 State에 포함)
    violated_rules: List[Dict[str, Any]]
    llm_reasoning: str
    confidence_score: float
    retrieved_legal_rules: list[Dict[str, Any]]  # 캐싱용: 한 번 검색한 규칙 재사용


# Supabase 클라이언트 (선택적 - Rule DB가 없으면 Mock 사용)
try:
    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )
    SUPABASE_AVAILABLE = True
    print("[Info] Supabase 연결 성공")
except:
    print("[Warning] Supabase 연결 실패. Mock 규칙 사용")
    supabase = None
    SUPABASE_AVAILABLE = False

openai_client = OpenAI(api_key=settings.openai_api_key)

# 전역 캐시
ALL_RULE_KEYWORDS = None


# ===== Mock 규칙 데이터 (Supabase Rule DB 없을 때 사용) =====
MOCK_RULES = [
    {
        "id": "mock_001",
        "rule_title": "비기능성 제품의 기능성 효과 광고 금지",
        "rule_type": "FUNCTIONAL_CLAIM",
        "severity": "HIGH",
        "rule_description": "일반 화장품은 미백, 주름개선, 자외선차단 등 기능성 효과를 광고할 수 없음",
        "keywords": ["미백", "화이트닝", "whitening", "주름개선", "주름완화", "링클", "wrinkle", "SPF", "PA", "자외선차단"],
        "prohibited_examples": ["미백 효과", "주름 개선", "SPF50", "자외선차단"],
        "allowed_examples": ["환한 피부", "화사한 피부", "탄력있는 피부"],
        "priority": 100,
        "regulation_categories": {
            "legal_basis": "화장품법 제13조",
            "category_name": "기능성 화장품"
        }
    },
    {
        "id": "mock_002",
        "rule_title": "질병 치료 효능 표시 금지",
        "rule_type": "MEDICAL_CLAIM",
        "severity": "HIGH",
        "rule_description": "화장품은 질병 치료, 완치, 개선 등의 의학적 효능을 표시할 수 없음",
        "keywords": ["치료", "완치", "질병", "질환", "증상", "개선", "여드름 치료", "아토피 치료"],
        "prohibited_examples": ["여드름 치료", "아토피 완치", "피부 질환 개선"],
        "allowed_examples": ["여드름 피부 케어", "트러블 케어", "민감 피부 케어"],
        "priority": 100,
        "regulation_categories": {
            "legal_basis": "화장품법 제13조",
            "category_name": "의학적 표현"
        }
    }
]


# ===== 유틸리티 함수 =====
def get_embedding(text: str) -> List[float]:
    """텍스트를 벡터로 변환"""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"[Error] 임베딩 생성 실패: {e}")
        return []


def load_all_keywords() -> List[str]:
    """Rule DB의 모든 키워드 로드 (한 번만)"""
    global ALL_RULE_KEYWORDS
    
    if ALL_RULE_KEYWORDS is not None:
        return ALL_RULE_KEYWORDS
    
    if SUPABASE_AVAILABLE:
        try:
            result = supabase.from_("regulation_rules") \
                .select("keywords") \
                .eq("is_active", True) \
                .execute()
            
            all_keywords = []
            for rule in result.data:
                keywords = rule.get("keywords", [])
                all_keywords.extend(keywords)
            
            ALL_RULE_KEYWORDS = sorted(set(all_keywords), key=len, reverse=True)
            print(f"[키워드 캐싱] {len(ALL_RULE_KEYWORDS)}개 키워드 로드됨")
            return ALL_RULE_KEYWORDS
        except Exception as e:
            print(f"[Warning] Rule DB 키워드 로드 실패: {e}")
    
    # Fallback: Mock 규칙에서 키워드 추출
    all_keywords = []
    for rule in MOCK_RULES:
        all_keywords.extend(rule.get("keywords", []))
    
    ALL_RULE_KEYWORDS = sorted(set(all_keywords), key=len, reverse=True)
    print(f"[키워드 캐싱] Mock에서 {len(ALL_RULE_KEYWORDS)}개 키워드 로드됨")
    return ALL_RULE_KEYWORDS


def extract_keywords_direct_matching(text: str) -> List[str]:
    """Rule DB의 키워드를 text에서 직접 찾기"""
    all_keywords = load_all_keywords()
    text_lower = text.lower()
    
    matched = []
    for keyword in all_keywords:
        if keyword.lower() in text_lower:
            matched.append(keyword)
    
    return matched


def retrieve_relevant_rules_improved(message: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """개선된 RAG: 직접 매칭 + 벡터 검색"""
    
    if not SUPABASE_AVAILABLE:
        # Supabase 없으면 Mock 규칙 반환
        print("[Info] Supabase 없음, Mock 규칙 사용")
        keywords = extract_keywords_direct_matching(message)
        if keywords:
            return MOCK_RULES
        return []
    
    # 1. 벡터 유사도 검색
    message_embedding = get_embedding(message)
    vector_results_data = []
    
    if message_embedding:
        try:
            vector_results = supabase.rpc(
                "match_regulation_rules",
                {
                    "query_embedding": message_embedding,
                    "match_threshold": 0.5,
                    "match_count": top_k
                }
            ).execute()
            vector_results_data = vector_results.data
        except Exception as e:
            print(f"[Warning] RPC 함수 오류: {str(e)}")
    
    # 2. 키워드 매칭 검색
    keywords = extract_keywords_direct_matching(message)
    print(f"[키워드 추출] {len(keywords)}개: {keywords[:10]}")
    
    keyword_results_data = []
    if keywords:
        try:
            keyword_results = supabase.from_("regulation_rules") \
                .select("*, regulation_categories(*)") \
                .overlaps("keywords", keywords) \
                .eq("is_active", True) \
                .order("priority", desc=True) \
                .limit(top_k * 2) \
                .execute()
            keyword_results_data = keyword_results.data
        except Exception as e:
            print(f"[Warning] 키워드 검색 오류: {str(e)}")
    
    # 3. 결과 병합
    all_rules = {}
    for rule in vector_results_data + keyword_results_data:
        rule_id = rule["id"]
        if rule_id not in all_rules:
            all_rules[rule_id] = rule
    
    sorted_rules = sorted(
        all_rules.values(),
        key=lambda x: x.get("priority", 0),
        reverse=True
    )
    
    print(f"[규칙 검색] {len(sorted_rules)}개 규칙 발견")
    return sorted_rules[:top_k]


def extract_legal_info_from_product(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    product_data에서 legal_info 추출
    Supabase legal_info 테이블에서 제품의 법적 정보 조회
    """
    product_id = product_data.get("product_id", "")
    
    if not product_id:
        print("[Warning] product_id가 없어 Mock 데이터 반환")
        return {
            "functional_status": None,
            "functional_types": [],
            "all_ingredients": product_data.get("description_short", "정보 없음"),
            "precautions": "1. 화장품 사용 시 이상이 있는 경우 전문의 상담",
            "volume_weight": "50ml"
        }
    
    if not SUPABASE_AVAILABLE:
        print("[Warning] Supabase 연결 불가, Mock 데이터 반환")
        return {
            "functional_status": None,
            "functional_types": [],
            "all_ingredients": product_data.get("description_short", "정보 없음"),
            "precautions": "1. 화장품 사용 시 이상이 있는 경우 전문의 상담",
            "volume_weight": "50ml"
        }
    
    try:
        result = supabase.from_("legal_info") \
            .select("functional_status, functional_type, all_ingredients, precautions, volume_weight") \
            .eq("product_code", str(product_id)) \
            .execute()
        
        if result.data and len(result.data) > 0:
            legal_data = result.data[0]
            return {
                "functional_status": legal_data.get("functional_status"),
                "functional_types": legal_data.get("functional_type", []) if legal_data.get("functional_type") else [],
                "all_ingredients": legal_data.get("all_ingredients", "정보 없음"),
                "precautions": legal_data.get("precautions", "정보 없음"),
                "volume_weight": legal_data.get("volume_weight", "정보 없음")
            }
        else:
            print(f"[Warning] legal_info 테이블에 product_code={product_id} 데이터 없음, Mock 반환")
            return {
                "functional_status": None,
                "functional_types": [],
                "all_ingredients": product_data.get("description_short", "정보 없음"),
                "precautions": "1. 화장품 사용 시 이상이 있는 경우 전문의 상담",
                "volume_weight": "50ml"
            }
            
    except Exception as e:
        print(f"[Warning] Supabase 법적 정보 조회 실패: {e}")
        return {
            "functional_status": None,
            "functional_types": [],
            "all_ingredients": product_data.get("description_short", "정보 없음"),
            "precautions": "1. 화장품 사용 시 이상이 있는 경우 전문의 상담",
            "volume_weight": "50ml"
        }


def build_compliance_prompt(
    message: str,
    product_info: Dict[str, Any],
    legal_info: Dict[str, Any],
    rules: List[Dict[str, Any]]
) -> str:
    """LLM에게 전달할 프롬프트 구성"""
    functional_status = legal_info.get("functional_status", "")
    functional_types = legal_info.get("functional_types", [])
    # 기능성 타입 매핑
    functional_type_names = {
        "WHITENING": "미백",
        "WRINKLE": "주름개선", 
        "UV_PROTECTION": "자외선차단",
        "HAIR_LOSS": "탈모 증상 완화"
    }
    
    approved_functions = [functional_type_names.get(ft, ft) for ft in functional_types]
    
    prompt = f"""
당신은 화장품법 전문가입니다. 주어진 화장품 마케팅 메시지가 대한민국 화장품법을 준수하는지 검수해주세요.

=== 검수 대상 메시지 ===
{message}

=== 제품 정보 ===
- 기능성 화장품 여부: {functional_status if functional_status else "일반 화장품 (비기능성)"}
"""
    
    # 기능성 화장품인 경우
    if functional_status and "필함" in functional_status:
        if not functional_types:
            prompt += """
- 심사받은 기능성 타입: ⚠️ 알 수 없음

⚠️ **매우 중요: 보수적 검수 모드**
이 제품은 기능성 화장품이지만 구체적인 기능성 타입을 확인할 수 없습니다.
따라서 **모든 기능성 관련 표현(미백, 주름개선, 자외선차단, 탈모)을 금지**합니다.

보수적 검수 원칙:
❌ 금지: "미백", "화이트닝", "주름개선", "SPF", "PA", "자외선차단", "탈모" 등 모든 기능성 표현
✅ 허용: "피부 보습", "피부 진정", "촉촉한 피부" 등 일반적 표현만 가능
"""
        else:
            prompt += f"""
- 심사받은 기능성 타입: {', '.join(approved_functions)}

⚠️ **중요: 기능성 타입 제한**
이 제품은 {', '.join(approved_functions)} 기능성 제품입니다.
- {', '.join(approved_functions)}에 대해서만 광고 가능합니다.
- 다른 기능성 효과는 일체 광고 불가능합니다.

광고 가능 표현:
"""
            
            # 각 기능성 타입별 허용 표현
            if "WHITENING" in functional_types:
                prompt += "✅ 미백: '미백', '화이트닝', '기미·주근깨 완화', '피부톤 개선'\n"
            else:
                prompt += "❌ 미백: 모든 미백 관련 표현 금지\n"
            
            if "WRINKLE" in functional_types:
                prompt += "✅ 주름개선: '주름 완화', '주름 개선', '링클 케어', '탄력'\n"
            else:
                prompt += "❌ 주름개선: 모든 주름 관련 표현 금지\n"
            
            if "UV_PROTECTION" in functional_types:
                prompt += "✅ 자외선차단: '자외선 차단', 'SPF', 'PA', 'UV 보호'\n"
            else:
                prompt += "❌ 자외선차단: SPF, PA, 자외선차단 표현 금지\n"
    else:
        prompt += """
- 심사받은 기능성 타입: 없음 (일반 화장품)

⚠️ **중요: 비기능성 제품**
이 제품은 일반 화장품으로 기능성 효과를 일체 광고할 수 없습니다.

❌ 절대 금지: "미백", "화이트닝", "주름개선", "링클", "SPF", "PA", "자외선차단", "탈모" 등
✅ 허용: "피부 보습", "피부 진정", "촉촉한 피부", "피부결 정돈" 등 일반 표현
"""
    
    prompt += f"""
- 전성분: {legal_info.get("all_ingredients", "정보 없음")[:200]}...
- 사용 시 주의사항: {legal_info.get("precautions", "정보 없음")[:100]}...

=== 적용할 규제 규칙 ===
"""
    
    # 검색된 규칙들 추가
    for idx, rule in enumerate(rules, 1):
        category = rule.get("regulation_categories") or {}
        prompt += f"""
[규칙 {idx}] {rule.get('rule_title', '제목 없음')}
- 법적 근거: {category.get('legal_basis', 'N/A')}
- 심각도: {rule.get('severity', 'N/A')}
- 설명: {rule.get('rule_description', '설명 없음')}
- 금지 예시: {', '.join(rule.get('prohibited_examples', [])[:3])}
- 허용 예시: {', '.join(rule.get('allowed_examples', [])[:3])}
---
"""
    
    prompt += """
=== 검수 요청사항 ===

**매우 중요: 검수 기준**

1. **직접적인 금지 키워드만 위반으로 판단하세요**
   - ✅ 위반: "미백", "화이트닝", "주름개선", "링클", "SPF", "PA" 등 명시적 키워드
   - ❌ 위반 아님: "환하게", "밝게", "화사하게", "맑은", "탄력있는" 등 일상적 표현

2. **비기능성 제품 금지어**
   - 미백: "미백", "화이트닝", "whitening"
   - 주름: "주름개선", "주름완화", "링클", "wrinkle"
   - 자외선: "SPF", "PA", "자외선차단", "UV차단"
   - 기미·주근깨: "기미", "주근깨"

3. **여드름 관련**
   - 금지: "여드름 치료", "여드름 제거", "여드름 완치"
   - 허용: "여드름 피부 케어", "트러블 케어"

=== 응답 형식 (JSON) ===
{
  "passed": true/false,
  "violated_rules": [
    {
      "rule_id": "규칙 ID",
      "rule_title": "위반한 규칙 제목",
      "violated_expression": "메시지에서 위반한 구체적 표현",
      "reason": "위반 이유",
      "severity": "HIGH/MEDIUM/LOW"
    }
  ],
  "reasoning": "전체 판단 근거",
  "confidence": 0.0~1.0,
  "suggestions": "위반 시 수정 제안"
}

**중요**: 명시적 금지 키워드가 없으면 passed: true
"""
    
    return prompt


def call_llm_judge(prompt: str) -> Dict[str, Any]:
    """OpenAI API를 호출하여 LLM 판단 받기"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 대한민국 화장품법 전문가입니다. 화장품 표시·광고가 법규를 준수하는지 정확하게 판단합니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        print(f"[LLM 판단 결과] {result}")
        return result
    except Exception as e:
        print(f"[Error] LLM 호출 실패: {e}")
        return {
            "passed": True,  # 오류 시 통과 처리 (또는 False로 보수적 처리)
            "violated_rules": [],
            "reasoning": f"LLM 호출 오류: {str(e)}",
            "confidence": 0.0,
            "suggestions": ""
        }


def save_compliance_history(
    product_id: str,
    message: str,
    passed: bool,
    violated_rules: List[Dict],
    llm_reasoning: str,
    confidence: float,
    retry_count: int
):
    """컴플라이언스 체크 히스토리 저장"""
    if not SUPABASE_AVAILABLE:
        return
    
    try:
        supabase.table("compliance_check_history").insert({
            "product_id": product_id,
            "message_content": message,
            "passed": passed,
            "violated_rules": violated_rules,
            "llm_reasoning": llm_reasoning,
            "confidence_score": confidence,
            "retry_count": retry_count
        }).execute()
    except Exception as e:
        print(f"[Warning] 히스토리 저장 실패: {e}")


# ===== LangGraph 노드 함수 =====
def compliance_check_node(state: GraphState) -> GraphState:
    """
    컴플라이언스 검수 노드
    
    프로세스:
    1. Rule DB에서 관련 규칙 검색 (RAG)
    2. product_data를 product_info와 legal_info로 변환 (로컬 변수)
    3. OpenAI API로 LLM 판단
    4. 통과/실패 결정
    """
    
    message = state["message"]
    product_data = state.get("product_data", {})
    retry_count = state.get("retry_count", 0)
    
    print(f"🔍 [Compliance Check] 검수 시작 (시도 {retry_count + 1}/5)")
    
    # 1. product_data를 product_info와 legal_info로 변환 (로컬 변수, 다른 노드와 공유 안 함)
    product_info = {
        "id": product_data.get("product_id", "unknown"),
        "name": product_data.get("name", ""),
        "brand": product_data.get("brand", ""),
        "category": product_data.get("category", {})
    }
    
    legal_info = extract_legal_info_from_product(product_data)
    
    # 2. Rule DB에서 관련 규칙 검색 (첫 방문 시에만, 이후엔 캐시 사용)
    retrieved_legal_rules = state.get("retrieved_legal_rules", [])
    
    if not retrieved_legal_rules:
        # 첫 방문: DB에서 규칙 검색 후 State에 캐싱
        relevant_rules = retrieve_relevant_rules_improved(message, top_k=15)
        
        # embedding 필드 제거하여 State 크기 최소화 (임베딩은 1536차원 벡터로 ~12KB/규칙)
        rules_without_embedding = [
            {k: v for k, v in rule.items() if k != "embedding"}
            for rule in relevant_rules
        ]
        state["retrieved_legal_rules"] = rules_without_embedding
        
        print(f"  - Retrieved Rules (첫 조회): {len(relevant_rules)}개 규칙 검색됨")
    else:
        # 재시도: 캐시된 규칙 재사용
        relevant_rules = retrieved_legal_rules
        print(f"  - Retrieved Rules (캐시 사용): {len(relevant_rules)}개 규칙 재사용")
    
    # 3. LLM 판단 프롬프트 구성
    prompt = build_compliance_prompt(message, product_info, legal_info, relevant_rules)
    
    # 4. OpenAI API 호출
    try:
        llm_result = call_llm_judge(prompt)
        
        passed = llm_result.get("passed", False)
        violated_rules = llm_result.get("violated_rules", [])
        reasoning = llm_result.get("reasoning", "")
        confidence = llm_result.get("confidence", 0.0)
        
        print(f"  - LLM Judgment: Passed={passed}, Confidence={confidence}")
        
        # 5. 히스토리 저장
        save_compliance_history(
            product_info["id"], message, passed, violated_rules,
            reasoning, confidence, retry_count
        )
        
        # 6. State 업데이트
        state["compliance_passed"] = passed
        state["violated_rules"] = violated_rules
        state["llm_reasoning"] = reasoning
        state["confidence_score"] = confidence
        
        # 실패 시 재시도 카운트 증가 및 error_reason 업데이트
        if not passed:
            state["retry_count"] = retry_count + 1

            if state["retry_count"] >= settings.max_retry_count:
                print(f"  ❌ [Compliance Check] 최대 재시도 횟수 도달. 최종 실패 처리.")
                state["compliance_passed"] = False
                
            
            # error_reason 업데이트: LLM reasoning + 위반 규칙 요약
            violation_summary = "\n".join([
                f"- {rule.get('rule_title')}: '{rule.get('violated_expression')}' (이유: {rule.get('reason')})"
                for rule in violated_rules
            ])
            
            state["error_reason"] = f"""
[화장품법 위반 감지]

{reasoning}

[위반 규칙 상세]
{violation_summary}

[수정 제안]
{llm_result.get('suggestions', '위반 표현을 제거하고 합법적 표현으로 대체하세요.')}
"""
            
            print("\n" + "="*80)
            print(f"❌ [Compliance Check FAILED] - 시도 {retry_count + 1}/5")
            print("="*80)
            print(f"위반 규칙: {len(violated_rules)}개 발견")
            print(f"신뢰도: {confidence:.2%}")
            print("\n[위반 내역]")
            for idx, rule in enumerate(violated_rules, 1):
                print(f"  {idx}. {rule.get('rule_title')}")
                print(f"     위반 표현: '{rule.get('violated_expression')}'")
                print(f"     심각도: {rule.get('severity')}")
                print(f"     이유: {rule.get('reason')}")
            print("\n[LLM 판단 근거]")
            print(f"{reasoning}")
            print("="*80 + "\n")
        else:
            state["error_reason"] = ""  # 성공 시 초기화
            print("\n" + "="*80)
            print(f"✅ [Compliance Check PASSED] - 시도 {retry_count + 1}/5")
            print("="*80)
            print(f"신뢰도: {confidence:.2%}")
            print(f"\n[LLM 판단 근거]\n{reasoning}")
            print("="*80 + "\n")
        
        return state
    
    except Exception as e:
        print(f"  ❌ [Error] 컴플라이언스 체크 중 오류: {str(e)}")
        state["compliance_passed"] = False
        state["violated_rules"] = [{
            "rule_title": "시스템 오류",
            "violated_expression": "검수 시스템 오류",
            "reason": str(e),
            "severity": "HIGH"
        }]
        state["llm_reasoning"] = f"시스템 오류 발생: {str(e)}"
        state["confidence_score"] = 0.0
        return state
