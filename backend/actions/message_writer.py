"""
Message Writer Node
OpenAI GPT-5 API를 사용한 메시지 생성
"""
from typing import TypedDict
from services.llm_client import llm_client
from utils.prompt_loader import load_prompt_template
from models.user import CustomerProfile

class GraphState(TypedDict):
    """LangGraph State 정의"""
    user_id: str
    user_data: CustomerProfile
    persona_id: Optional[str]
    intention: str
    strategy: int  # orchestrator에서 결정한 케이스 (1-4)
    recommended_product_id: str
    product_data: dict
    brand_tone: dict
    channel: str
    message: str
    compliance_passed: bool
    retry_count: int
    error: str
    error_reason: str  # Compliance 실패 이유
    success: bool  # API 응답용


async def message_writer_node(state: GraphState) -> GraphState:
    """
    Message Writer Node
    
    OpenAI GPT API를 호출하여 개인화된 메시지를 생성합니다.
    """
    strategy = state["strategy"]
    user_data = state["user_data"]
    product_data = state["product_data"]
    brand_tone = state["brand_tone"]
    intention = state.get("intention", "GENERAL")
    channel = state.get("channel", "APPPUSH")
    retry_count = state.get("retry_count", 0)
    error_reason = state.get("error_reason", "")  # Compliance 실패 이유 가져오기
    
    import json
    import os

    # print(f"🖋️ Message Writer Node 시작... {state}")

    # 1. 프롬프트 템플릿 로드
    prompt_config = load_prompt_template("writer_prompt.yaml")
    # Base Template (Identity only, or empty if fully replaced)
    # 기존 템플릿의 {brand_name}, {tone_style} 부분은 아래 로직으로 대체됨
    
    user_prompt_template = prompt_config["user"]
    
    # CRM Guideline Load
    guideline_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services/crm_guideline.json")
    try:
        with open(guideline_path, "r", encoding="utf-8") as f:
            crm_guidelines = json.load(f)
    except FileNotFoundError:
        crm_guidelines = {"brands": {}, "groups": {}}

    brand_name = product_data['brand']
    print("check point 1 - brand_name:", brand_name)
    
    # Dynamic System Prompt Construction
    if brand_name in crm_guidelines["brands"]:
        brand_cfg = crm_guidelines["brands"][brand_name]
        group_cfg = crm_guidelines["groups"][brand_cfg["group"]]
        
        system_prompt = f"""
당신은 {brand_name}의 전문 CRM 카피라이터입니다.

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
        # Fallback to Legacy Logic
        print(f"⚠️ {brand_name}에 대한 CRM 가이드라인이 없습니다. 기본 템플릿을 사용합니다.")
        system_prompt_template = prompt_config["system"]
        tone_examples = "\n".join(f"- {ex}" for ex in brand_tone.get("tone_manner_examples", []))
        
        system_prompt = system_prompt_template.format(
            brand_name=brand_name,
            tone_style=brand_tone['tone_manner_style'],
            tone_examples=tone_examples
        )

    # [중요] 캠페인 의도(Intention) 반영
    intention_guides = {
        "GENERAL": "일상적인 안부와 함께 자연스럽게 상품을 추천하세요.",
        "EVENT": "현재 진행 중인 특별한 혜택이나 이벤트를 강조하여 구매를 유도하세요.",
        "WEATHER": "현재 날씨나 계절적 특성을 언급하며 그에 맞는 피부 관리법을 제안하세요."
    }
    intention_context = intention_guides.get(intention, intention_guides["GENERAL"])
    system_prompt += f"\n\n[캠페인 의도]\n{intention_context}"

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
        print(f"🔄 [Retry {retry_count}] 이전 거부 이유를 프롬프트에 포함시켰습니다.")

    # 2. 채널 제한 텍스트 결정 (Restored)
    channel_limits = {
        "APPPUSH": "50자 이내",
        "KAKAO": "1000자 이내 (첫 문장 30자 이내 권장)",
        "EMAIL": "제한 없음 (단, 핵심 메시지는 첫 200자 이내)",
    }
    limit = channel_limits.get(channel, "적절한 길이")
    
    # 3. 전략 변수 설정 (Orchestrator int 입력 대응)
    strategy_input = state["strategy"]
    persona_id = state.get("persona_id")
    
    # 기본값 설정
    persona_name = "Trend Setter"
    communication_tone = "Casual & Trendy"
    message_goal = "Product Recommendation"

    # 페르소나 DB 로드 (필요시)
    if persona_id:
        persona_db_path = os.path.join(os.path.dirname(__file__), "../services/recsys/persona_db.json")
        try:
            with open(persona_db_path, "r", encoding="utf-8") as f:
                persona_db = json.load(f)
                if persona_id in persona_db:
                    p_data = persona_db[persona_id]
                    persona_name = p_data.get("persona_name", persona_name)
                    communication_tone = p_data.get("tone", communication_tone)
                    # 키워드 등을 목표에 추가 반영 가능
        except Exception:
            pass
    
    if isinstance(strategy_input, int):
        # Orchestrator가 Case(int)를 반환하는 경우 Goal 매핑
        goals = {
            0: "Best Seller Recommendation (Cold Start)",
            1: "Interest-based Recommendation (Behavioral)", 
            2: "Personalized Recommendation (Profile-based)",
            3: "Repurchase Reminder (Hybrid)"
        }
        message_goal = goals.get(strategy_input, "Product Recommendation")
    elif isinstance(strategy_input, dict):
        # Dict 형태인 경우 (Future Proof)
        persona_name = strategy_input.get("persona_name", persona_name)
        message_goal = strategy_input.get("message_goal", message_goal)
        communication_tone = strategy_input.get("communication_tone", communication_tone)

    user_prompt = user_prompt_template.format(
        user_name=user_data.name,
        age_group=user_data.age_group,
        membership_level=user_data.membership_level,
        skin_type=', '.join(user_data.skin_type),
        skin_concerns=', '.join(user_data.skin_concerns),
        last_purchase=user_data.last_purchase.product_name if user_data.last_purchase else '없음',
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
        limit_text=limit
    )
    
    try:
        # 4. LLM 호출
        result = llm_client.generate_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        generated_message = result["content"]
        print("📝 Generated Message:\n", generated_message)
        usage = result["usage"]
        
        # 5. 비용 계산 (GPT-4 기준: Input $0.03/1k, Output $0.06/1k)
        # Note: 모델 버전에 따라 가격이 다를 수 있음. 기본 GPT-4 가격 적용.
        input_cost = (usage["prompt_tokens"] / 1000) * 0.03
        output_cost = (usage["completion_tokens"] / 1000) * 0.06
        total_cost = input_cost + output_cost
        
        state["message"] = generated_message
        state["error"] = ""

        
    except Exception as e:
        state["error"] = f"메시지 생성 중 오류 발생: {str(e)}"
    
    return state