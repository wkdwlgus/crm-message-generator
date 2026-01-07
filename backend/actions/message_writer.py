"""
Message Writer Node
OpenAI GPT-5 API를 사용한 메시지 생성
"""
from typing import TypedDict
from services.llm_client import llm_client
from services.crm_history_service import crm_history_service
from utils.prompt_loader import load_prompt_template
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
    weather: str  # [NEW]
    intent: str   # [NEW]
    compliance_passed: bool
    retry_count: int
    error: str
    error_reason: str  # Compliance 실패 이유
    success: bool  # API 응답용
    retrieved_legal_rules: list  # 캐싱용: Compliance 노드에서 한 번 검색한 규칙 재사용
    # Optional inputs from Orchestrator that might be used here
    crm_reason: str
    target_persona: str


def message_writer_node(state: GraphState) -> GraphState:
    """
    Message Writer Node with history reuse
    
    OpenAI GPT API를 호출하여 개인화된 메시지를 생성합니다.
    """
    user_data = state["user_data"]
    product_data = state["product_data"]
    brand_tone = state["brand_tone"]
    channel = state.get("channel", "APPPUSH")
    retry_count = state.get("retry_count", 0)
    error_reason = state.get("error_reason", "")
    
    # [NEW] Context Variables
    weather = state.get("weather", "Sunny")
    intent = state.get("intent", "Discovery")
    brand_name = product_data['brand']
    persona_name = "Trend Setter" # Default
    
    # 전략에서 persona 추출 (Optional)
    if "target_persona" in state:
        persona_name = state["target_persona"]
    
    beauty_profile = {
        "skin_type": user_data.skin_type,
        "skin_concerns": user_data.skin_concerns,
        "keywords": user_data.keywords,
        "preferred_tone": user_data.preferred_tone
    }

    print(f"🧐 CRM Cache Check: {brand_name}, {persona_name}, {intent}, {weather}")

    # 1. CRM History Cache Check
    cached_msg = crm_history_service.find_message(
        brand=brand_name,
        persona=persona_name,
        intent=intent,
        weather=weather,
        beauty_profile=beauty_profile
    )
    
    if cached_msg and retry_count == 0:
        print("⚡️ CRM Cache Hit! Reusing message.")
        state["message"] = cached_msg
        state["error"] = ""
        state["success"] = True
        return state

    import json
    import os

    # 2. 프롬프트 템플릿 로드
    prompt_config = load_prompt_template("writer_prompt.yaml")
    
    user_prompt_template = prompt_config["user"]
    
    # CRM Guideline Load
    guideline_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services/crm_guideline.json")
    try:
        with open(guideline_path, "r", encoding="utf-8") as f:
            crm_guidelines = json.load(f)
    except FileNotFoundError:
        crm_guidelines = {"brands": {}, "groups": {}}

    
    # Dynamic System Prompt Construction
    if brand_name in crm_guidelines["brands"]:
        brand_cfg = crm_guidelines["brands"][brand_name]
        group_cfg = crm_guidelines["groups"][brand_cfg["group"]]
        
        system_prompt = f"""
당신은 {brand_name}의 전문 CRM 카피라이터입니다.

[상황 정보]
- 고객 의도: {intent}
{f'- 날씨: {weather}' if intent == 'weather' and weather else ''}

[그룹 가이드라인: {brand_cfg["group"]}]
톤: {group_cfg["tone"]}
규칙:
- {"\n- ".join(group_cfg["rules"])}

[브랜드 가이드라인]
타겟: {brand_cfg["target"]}
키워드: {", ".join(brand_cfg["keywords"])}
전략: {brand_cfg["focus"]}
"""
    else:
        print(f"⚠️ {brand_name}에 대한 CRM 가이드라인이 없습니다. 기본 템플릿을 사용합니다.")
        system_prompt_template = prompt_config["system"]
        tone_examples = "\n".join(f"- {ex}" for ex in brand_tone.get("tone_manner_examples", []))
        
        system_prompt = system_prompt_template.format(
            brand_name=brand_name,
            tone_style=brand_tone['tone_manner_style'],
            tone_examples=tone_examples
        )
        
        # [MODIFIED] intent에 따라 추가 프롬프트 분기
        if intent == "weather" and weather:
            system_prompt += f"\n\n[추가 상황 - 날씨]\n현재 날씨: {weather}\n(날씨에 맞는 톤앤매너와 제품 추천 멘트를 녹여내세요.)"
        
        system_prompt += f"\n\n[고객 의도]\n{intent}"

    # 재시도인 경우 Compliance 실패 이유를 프롬프트에 추가
    if retry_count > 0 and error_reason:
        system_prompt += f"""

⚠️ **중요: 이전 메시지가 화장품법 위반으로 거부되었습니다**
재시도 횟수: {retry_count}/5

[이전 거부 이유]
{error_reason}

**반드시 위 문제를 해결한 메시지를 작성하세요:**
- 위반했던 표현을 절대 사용하지 마세요
- 대체 가능한 합법적 표현을 사용하세요
- 화장품법 준수를 최우선으로 하세요
"""
    

    # 3. 채널별 상세 가이드라인 설정 [NEW]
    CHANNEL_CONFIG = {
        "APP_PUSH": {
            "title_token_limit": 50,
            "body_token_limit": 125,
            "structure": "① Title (Hook)\n② Body (Benefit + Emoji)",
            "guidelines": [
                "Use emojis to grab attention.",
                "Focus on immediate benefit.",
                "Keep it very short and punchy."
            ]
        },
        "SMS": {
            "title_token_limit": 100,
            "body_token_limit": 600,
            "structure": "① Title (Clear Topic)\n② Body (Main Message)\n③ CTA (Link)",
            "guidelines": [
                "No special formatting (plain text only).",
                "Get straight to the point.",
                "Include a clear call to action link."
            ]
        },
        "EMAIL": {
            "title_token_limit": 50,
            "body_token_limit": 600,
            "structure": "① 공감/상황 제시 (1~2문장)\n② 개인화 포인트 (피부/날씨/이력)\n③ 제안 or 혜택\n④ CTA (링크/버튼 유도)",
            "guidelines": [
                "Use a professional yet engaging tone.",
                "Clearly separate sections.",
                "Focus on the 'Why' for the customer."
            ]
        },
        "KAKAO": {
            "title_token_limit": 100,
            "body_token_limit": 600,
            "structure": "① Title (Eye-catching)\n② Greeting (Personalized)\n③ Key Benefit (Bulleted List)\n④ CTA",
            "guidelines": [
                "Use bullet points for readability.",
                "Friendly and approachable tone.",
                "Highlight key benefits clearly."
            ]
        }
    }
    
    # 해당 채널 설정 가져오기 (없으면 APP_PUSH 기본값)
    ch_cfg = CHANNEL_CONFIG.get(channel, CHANNEL_CONFIG["APP_PUSH"])
    
    limit_text = f"""
- 제목 길이: 최대 {ch_cfg['title_token_limit']} 토큰 (약 {ch_cfg['title_token_limit']//2} 단어)
- 본문 길이: 최대 {ch_cfg['body_token_limit']} 토큰 (약 {ch_cfg['body_token_limit']//2} 단어)
- 필수 구조:
{ch_cfg['structure']}
- 작성 지침:
{chr(10).join(['  - ' + g for g in ch_cfg['guidelines']])}
"""

    
    # 4. 전략 변수 설정
    communication_tone = "Casual & Trendy"
    message_goal = "Product Recommendation"
    
    # strategy_input 로직 제거 및 기본값/상태값 사용
    # TODO: 추후 Orchestrator에서 구체적인 전략을 넘겨주면 매핑 로직 복구 가능

    user_prompt = user_prompt_template.format(
        skin_type=', '.join(user_data.skin_type),
        skin_concerns=', '.join(user_data.skin_concerns),
        product_name=product_data['name'],
        brand_name=product_data['brand'],
        discounted_price=f"{product_data['price']['discounted_price']:,}",
        discount_rate=product_data['price']['discount_rate'],
        product_desc=product_data['description_short'],
        review_keywords=', '.join(product_data['review']['top_keywords']),
        persona_name=persona_name,
        message_goal=message_goal,
        communication_tone=communication_tone,
        channel=channel,
        limit_text=limit_text # [MODIFIED] Detailed config text injected
    )
    
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
        usage = result["usage"]
        
        # 6. 비용 계산 (GPT-4 기준: Input $0.03/1k, Output $0.06/1k)
        # Note: 모델 버전에 따라 가격이 다를 수 있음. 기본 GPT-4 가격 적용.
        input_cost = (usage["prompt_tokens"] / 1000) * 0.03
        output_cost = (usage["completion_tokens"] / 1000) * 0.06
        total_cost = input_cost + output_cost
        
        state["message"] = generated_message
        state["error"] = ""
        
        # 7. [NEW] Save to CRM History (성공 시에만)
        if not error_reason: # 재시도가 아닐 때만 저장 (안전한 메시지만)
             crm_history_service.save_message(
                brand=brand_name,
                persona=persona_name,
                intent=intent,
                weather=weather,
                beauty_profile=beauty_profile,
                message_content=generated_message
            )

        
    except Exception as e:
        state["error"] = f"메시지 생성 중 오류 발생: {str(e)}"
    
    return state
