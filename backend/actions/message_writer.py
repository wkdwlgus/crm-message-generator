"""
Message Writer Node
OpenAI GPT-5 API를 사용한 메시지 생성
"""
from typing import TypedDict
from services.llm_client import llm_client
from models.user import CustomerProfile

class GraphState(TypedDict):
    """LangGraph State 정의"""
    user_id: str
    user_data: CustomerProfile
    recommended_product_id: str
    product_data: dict
    brand_tone: dict
    channel: str
    message: str
    message_template: str # [NEW] Placeholder 포함된 템플릿 메시지 (DB 저장용)
    compliance_passed: bool
    retry_count: int
    error: str
    error_reason: str  # Compliance 실패 이유
    success: bool  # API 응답용
    retrieved_legal_rules: list  # 캐싱용: Compliance 노드에서 한 번 검색한 규칙 재사용
    # RecSys Orchestrator Outputs
    crm_reason: str
    weather_detail: str
    target_brand: str
    target_persona: str
    recommended_brand: str


def message_writer_node(state: GraphState) -> GraphState:
    """
    Message Writer Node with history reuse
    OpenAI GPT API를 호출하여 개인화된 메시지를 생성합니다.
    """
    import json
    import os

    user_data = state["user_data"]
    product_data = state["product_data"]
    brand_tone = state["brand_tone"]
    channel = state.get("channel", "APPPUSH")
    retry_count = state.get("retry_count", 0)
    error_reason = state.get("error_reason", "")
    
    # RecSys Orchestrator Inputs
    crm_reason = state.get("crm_reason", "일반홍보")
    weather_detail = state.get("weather_detail", "")
    target_pid = state.get("target_persona", "4") # Default to '4'
    brand_name = product_data['brand']
    product_name = product_data['name']
    
    # 1. Intent & Persona Logic (New)
    # Intent Logic (Use crm_reason directly)
    intent = crm_reason
        
    weather = weather_detail if intent in ["날씨", "weather"] else ""
    
    # Load Persona DB
    base_path = os.path.dirname(os.path.dirname(__file__))
    persona_db_path = os.path.join(base_path, "actions/persona_db.json")
    try:
        with open(persona_db_path, "r", encoding="utf-8") as f:
            persona_db = json.load(f)
    except FileNotFoundError:
        persona_db = {}

    target_persona_data = persona_db.get(str(target_pid), {
        "persona_name": "Trend Setter", "description": "트렌드 민감", "tone": "트렌디", "keywords": []
    })
    persona_name = target_persona_data['persona_name']
    
    # [Cache Logic Removed: Moved to retrieve_crm_node]

    # 2. 설정 파일 로드 (Brand Guidelines)
    guideline_path = os.path.join(base_path, "services/crm_guideline.json")
    try:
        with open(guideline_path, "r", encoding="utf-8") as f:
            crm_guidelines = json.load(f)
    except FileNotFoundError:
        crm_guidelines = {"brands": {}, "groups": {}}

    # [Sender: Brand Persona]
    if brand_name in crm_guidelines["brands"]:
        brand_cfg = crm_guidelines["brands"][brand_name]
        group_cfg = crm_guidelines["groups"][brand_cfg["group"]]
        
        sender_context = f"""
[1. 화자: 브랜드 페르소나 (Sender)]
- 브랜드: {brand_name} (Group: {brand_cfg['group']})
- 톤앤매너: {group_cfg['tone']}
- 핵심 전략: {brand_cfg['focus']}
- 작성 원칙:
{chr(10).join(['  - ' + r for r in group_cfg['rules']])}
"""
    else:
        # Fallback
        sender_context = f"""
[1. 화자: 브랜드 페르소나 (Sender)]
- 브랜드: {brand_name}
- 톤앤매너: {brand_tone.get('tone_manner_style', '자연스러운')}
"""

    # [Receiver: Target Persona]
    receiver_context = f"""
[2. 청자: 타겟 페르소나 (Receiver)]
- 타겟명: {target_persona_data['persona_name']}
- 특징/니즈: {target_persona_data['description']}
- 선호 톤: {target_persona_data['tone']}
- 선호 키워드: {', '.join(target_persona_data['keywords'])}
"""

    # [Context: Situation]
    INTENT_DESCRIPTIONS = {
        "regular": "일반적인 앱 푸시 마케팅 (Daily Refresh)",
        "events": "할인 이벤트나 증정 행사 마케팅 (Promotional)",
        "weather": "계절 및 날씨 요인에 맞춘 마케팅 (Seasonal)",
        # Korean mapping from Orchestrator
        "일반홍보": "일반적인 앱 푸시 마케팅 (Daily Refresh)",
        "할인행사": "할인 이벤트나 증정 행사 마케팅 (Promotional)",
        "이벤트": "할인 이벤트나 증정 행사 마케팅 (Promotional)",
        "프로모션": "할인 이벤트나 증정 행사 마케팅 (Promotional)",
        "날씨": "계절 및 날씨 요인에 맞춘 마케팅 (Seasonal)",
        "신제품": "신제품 출시 홍보 (Launch)"
    }
    intent_desc = INTENT_DESCRIPTIONS.get(intent, "일반 마케팅")

    weather_context = f"- 날씨: {weather} (날씨에 맞는 멘트와 제품 추천을 자연스럽게 연결하세요)" if (intent in ["날씨", "weather"] and weather) else ""
    
    situation_context = f"""
[3. 상황 (Context)]
- 마케터 의도: {intent} ({intent_desc})
{weather_context}
"""

    # 4. 채널별 상세 가이드라인 설정
    CHANNEL_CONFIG = {
        "APP_PUSH": {
            "title_token_limit": 50,
            "body_token_limit": 100,
            "structure": "① 제목 (후킹 요소)\n② 본문 (혜택 + 이모지)",
            "guidelines": [
                "이모지를 사용하여 주목도를 높이세요.",
                "즉각적인 혜택에 집중하세요.",
                "매우 짧고 임팩트 있게 작성하세요."
            ]
        },
        "SMS": {
            "title_token_limit": 100,
            "body_token_limit": 600,
            "structure": "① 제목 (명확한 주제)\n② 본문 (핵심 메시지)\n③ CTA (링크)",
            "guidelines": [
                "특별한 서식 사용 금지 (텍스트만 사용).",
                "핵심 내용을 바로 전달하세요.",
                "명확한 행동 유도(CTA) 링크를 포함하세요."
            ]
        },
        "EMAIL": {
            "title_token_limit": 50,
            "body_token_limit": 600,
            "structure": "① 공감/상황 제시 (1~2문장)\n② 개인화 포인트 (피부/날씨/이력)\n③ 제안 or 혜택\n④ CTA (링크/버튼 유도)",
            "guidelines": [
                "전문적이면서도 매력적인 톤을 사용하세요.",
                "섹션을 명확히 구분하세요.",
                "고객이 얻을 수 있는 '이유'에 집중하세요."
            ]
        },
        "KAKAO": {
            "title_token_limit": 100,
            "body_token_limit": 600,
            "structure": "① 제목 (시선을 끄는 문구)\n② 인사말 (개인화)\n③ 핵심 혜택 (글머리 기호)\n④ CTA",
            "guidelines": [
                "가독성을 위해 글머리 기호를 사용하세요.",
                "친근하고 접근하기 쉬운 톤을 사용하세요.",
                "핵심 혜택을 명확하게 강조하세요."
            ]
        }
    }
    
    ch_cfg = CHANNEL_CONFIG.get(channel, CHANNEL_CONFIG["APP_PUSH"])
    
    channel_context = f"""
[4. 채널 제약 (Channel: {channel})]
- 제목 길이: 최대 {ch_cfg['title_token_limit']} 토큰 (약 {ch_cfg['title_token_limit']//2} 단어)
- 본문 길이: 최대 {ch_cfg['body_token_limit']} 토큰 (약 {ch_cfg['body_token_limit']//2} 단어)
- 필수 구조:
{ch_cfg['structure']}
- 작성 지침:
{chr(10).join(['  - ' + g for g in ch_cfg['guidelines']])}
"""

    # 5. 프롬프트 조합
    system_prompt = f"""
당신은 {brand_name}의 전문 CRM 카피라이터입니다.
브랜드의 목소리(Sender)를 유지하되, 타겟 고객(Receiver)의 니즈를 정조준하여 설득력 있는 메시지를 작성하세요.
**반드시 한국어(Korean)로 작성하세요.**

{sender_context}
{receiver_context}
{situation_context}
{channel_context}
"""

    # 재시도 처리
    if retry_count > 0 and error_reason:
        system_prompt += f"""
⚠️ **중요: 이전 메시지가 화장품법 위반으로 거부되었습니다**
재시도 횟수: {retry_count}/5
이전 거부 이유: {error_reason}
**반드시 위 문제를 해결한 메시지를 작성하세요:**
- 위반했던 표현을 절대 사용하지 마세요
- 대체 가능한 합법적 표현을 사용하세요
- 화장품법 준수를 최우선으로 하세요
"""

    # User Prompt 구성 (기본 정보 제공)
    user_prompt = f"""
다음 고객에게 보낼 퍼스널 메시지를 작성하세요.

[고객 프로필]
- 이름: {user_data.name} ({user_data.age_group}, {user_data.membership_level})
- 피부 특성: {', '.join(user_data.skin_type)}, {', '.join(user_data.skin_concerns)}
- 최근 관심: {', '.join(user_data.keywords)}

[추천 상품]
- 상품명: {product_data['name']}
- 브랜드: {product_data['brand']} ({product_data['price'].get('discount_rate', 0)}% 할인)
- 특징: {product_data['description_short']}
- 리뷰 반응: {', '.join(product_data['review']['top_keywords'])}

[작성 요청]
위 타겟 페르소나({target_persona_data['persona_name']})의 성향을 고려하여, 브랜드 톤앤매너로 메시지를 완성하세요.
구조와 분량을 반드시 준수하세요.
- 고객 이름은 반드시 `{{customer_name}}` 플레이스홀더를 사용하세요. (실사용 시 치환됨)
"""
    
    try:
        # 5. LLM 호출
        result = llm_client.generate_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=ch_cfg['body_token_limit'] + 100 # [NEW] Max Output Tokens Control
        )
        
        generated_message = result["content"]
        print("📝 Generated Message (Template):\n", generated_message)
        usage = result["usage"]
        
        # 6. 비용 계산 (GPT-4 기준: Input $0.03/1k, Output $0.06/1k)
        # Note: 모델 버전에 따라 가격이 다를 수 있음. 기본 GPT-4 가격 적용.
        input_cost = (usage["prompt_tokens"] / 1000) * 0.03
        output_cost = (usage["completion_tokens"] / 1000) * 0.06
        total_cost = input_cost + output_cost
        
        state["error"] = ""
        state["success"] = True
        state["message_template"] = generated_message # 템플릿 저장 (Compliance Node에서 사용)
        
        # 7. [MOVED] Save to CRM History는 Compliance Check 이후로 이동함
        # if not error_reason: ... (Moved to compliance_check.py)
        
        # 8. Placeholder 처리는 personalize_node에서 수행
        state["message"] = generated_message
        
    except Exception as e:
        state["error"] = f"메시지 생성 중 오류 발생: {str(e)}"
    
    return state