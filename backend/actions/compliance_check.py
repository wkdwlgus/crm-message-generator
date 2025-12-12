"""
Compliance Check Node
화장품법 준수 여부 검증
"""
from typing import TypedDict, List
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


# 화장품법 위반 금지 단어 리스트
PROHIBITED_WORDS = [
    # 절대적 효능 표현
    "완치", "치료", "개선", "회복", "재생",
    "100%", "즉시", "즉각", "바로", "단번에",
    "영구적", "영구", "영원히", "평생",
    
    # 의학적 표현
    "의학적", "임상적", "의사", "한의사", "약사",
    "처방", "진단", "질병", "질환", "증상",
    
    # 과장 광고
    "세계 최고", "국내 최고", "최고급", "최상급",
    "1등", "넘버원", "No.1", "#1",
    "혁명적", "기적", "마법",
    
    # 피부 질환 관련
    "아토피", "여드름 치료", "건선", "습진", "피부염",
    "알레르기 치료", "각질 제거",
]


def compliance_check_node(state: GraphState) -> GraphState:
    """
    Compliance Check Node
    
    생성된 메시지가 화장품법을 준수하는지 검증합니다.
    위반 시 재생성을 위해 compliance_passed를 False로 설정합니다.
    
    Args:
        state: LangGraph State
        
    Returns:
        업데이트된 GraphState
    """
    message = state.get("message", "")
    retry_count = state.get("retry_count", 0)
    
    # 금지 단어 검사
    violations = check_prohibited_words(message)
    
    if violations:
        # 위반 발견
        state["compliance_passed"] = False
        state["retry_count"] = retry_count + 1
        state["error"] = f"화장품법 위반 단어 발견: {', '.join(violations)}"
    else:
        # 통과
        state["compliance_passed"] = True
        state["error"] = ""
    
    return state


def check_prohibited_words(message: str) -> List[str]:
    """
    메시지에서 금지 단어 검사
    
    Args:
        message: 검사할 메시지
        
    Returns:
        발견된 금지 단어 리스트
    """
    violations = []
    
    for word in PROHIBITED_WORDS:
        if word.lower() in message.lower():
            violations.append(word)
    
    return violations
