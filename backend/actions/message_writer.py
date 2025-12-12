"""
Message Writer Node
OpenAI GPT-5 API를 사용한 메시지 생성
"""
from typing import TypedDict
import openai
from config import settings
from models.user import CustomerProfile


class GraphState(TypedDict):
    """LangGraph State 정의"""
    user_id: str
    user_data: CustomerProfile
    strategy: dict
    recommended_product_id: str
    product_data: dict
    brand_tone: dict
    channel: str
    message: str
    compliance_passed: bool
    retry_count: int
    error: str


def message_writer_node(state: GraphState) -> GraphState:
    """
    Message Writer Node
    
    OpenAI GPT API를 호출하여 개인화된 메시지를 생성합니다.
    
    Args:
        state: LangGraph State
        
    Returns:
        업데이트된 GraphState
    """
    strategy = state["strategy"]
    user_data = state["user_data"]
    product_data = state["product_data"]
    brand_tone = state["brand_tone"]
    channel = state.get("channel", "SMS")
    
    # OpenAI API 설정
    client = openai.OpenAI(api_key=settings.openai_api_key)
    
    # 프롬프트 생성
    prompt = build_prompt(strategy, user_data, product_data, brand_tone, channel)
    
    try:
        # GPT API 호출
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 한국 화장품 CRM 메시지 작성 전문가입니다. 고객 데이터와 브랜드 톤앤매너를 기반으로 개인화된 메시지를 한국어로 작성합니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500,
        )
        
        # 생성된 메시지 추출
        generated_message = response.choices[0].message.content.strip()
        state["message"] = generated_message
        
    except Exception as e:
        state["error"] = f"메시지 생성 중 오류 발생: {str(e)}"
    
    return state


def build_prompt(strategy: dict, user_data: CustomerProfile, product_data: dict, brand_tone: dict, channel: str) -> str:
    """
    GPT API 프롬프트 생성
    
    Args:
        strategy: 메시지 전략
        user_data: 고객 데이터
        product_data: 상품 데이터
        brand_tone: 브랜드 톤앤매너
        channel: 채널 (SMS, KAKAO, EMAIL)
        
    Returns:
        프롬프트 문자열
    """
    # 채널별 문자 수 제한
    channel_limits = {
        "SMS": "90자 이내",
        "KAKAO": "1000자 이내 (첫 문장 30자 이내 권장)",
        "EMAIL": "제한 없음 (단, 핵심 메시지는 첫 200자 이내)",
    }
    
    limit = channel_limits.get(channel, "적절한 길이")
    
    # 브랜드 톤앤매너 예시
    tone_examples = "\n".join(f"- {ex}" for ex in brand_tone.get("tone_manner_examples", []))
    
    prompt = f"""
고객 정보:
- 이름: {user_data.name}
- 연령대: {user_data.age_group}
- 멤버십 등급: {user_data.membership_level}
- 피부 타입: {', '.join(user_data.skin_type)}
- 피부 고민: {', '.join(user_data.skin_concerns)}
- 최근 구매 상품: {user_data.last_purchase.product_name if user_data.last_purchase else '없음'}
- 재구매 주기 알림: {'활성' if user_data.repurchase_cycle_alert else '비활성'}

추천 상품:
- 브랜드: {product_data['brand']}
- 상품명: {product_data['name']}
- 할인가: {product_data['price']['discounted_price']:,}원 ({product_data['price']['discount_rate']}% 할인)
- 평점: {product_data['review']['score']}/5.0 (리뷰 {product_data['review']['count']:,}개)
- 인기 키워드: {', '.join(product_data['review']['top_keywords'])}
- 설명: {product_data['description_short']}

메시지 전략:
- 페르소나: {strategy['persona_name']}
- 커뮤니케이션 톤: {strategy['communication_tone']}
- 디테일 레벨: {strategy['detail_level']}
- 메시지 목표: {strategy['message_goal']}

브랜드 톤앤매너:
- 스타일: {brand_tone['tone_manner_style']}
- 예시:
{tone_examples}

채널: {channel} ({limit})

위 정보를 바탕으로 {user_data.name} 고객에게 {product_data['name']}을(를) 추천하는 {channel} 메시지를 작성해주세요.

요구사항:
1. 브랜드의 톤앤매너를 반영할 것
2. 고객의 피부 타입과 고민을 언급할 것
3. 상품의 핵심 장점을 강조할 것
4. 할인 혜택을 명시할 것
5. {limit} 준수할 것
6. 한국어로만 작성할 것
7. 화장품법 준수 (절대적 효능 표현 금지, 과장 광고 금지)

메시지만 출력하고, 추가 설명은 하지 마세요.
"""
    
    return prompt
