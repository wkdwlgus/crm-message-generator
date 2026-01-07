
from actions.orchestrator import GraphState

def personalize_message_node(state: GraphState) -> GraphState:
    """
    Personalization Node
    메시지 템플릿(Cached or Generated)의 Placeholder를 실제 고객 이름으로 치환합니다.
    """
    print("\n" + "="*80)
    print("🎨 [Personalize Node] Applying User Context...")
    print("="*80)
    
    try:
        user_name = state["user_data"].name
        # Template이 우선, 없으면 이미 생성된 message 사용 (fallback)
        raw_msg = state.get("message_template") or state.get("message", "")
        
        if not raw_msg:
            print("⚠️ No message content to personalize.")
            return state
            
        # 다양한 Placeholder 패턴 처리
        final_msg = raw_msg.replace("{{customer_name}}", user_name) \
                           .replace("{customer_name}", user_name) \
                           .replace("{{Customer_Name}}", user_name) \
                           .replace("{Customer_Name}", user_name)
                           
        state["message"] = final_msg
        print(f"✅ Personalization Complete. Final Message Length: {len(final_msg)}")
        
    except Exception as e:
        print(f"⚠️ Personalization Failed: {e}")
        # 실패 시 원본 메시지라도 유지
        
    return state
