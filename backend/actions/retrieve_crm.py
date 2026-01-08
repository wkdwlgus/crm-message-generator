import json
from typing import Dict, Any
from actions.orchestrator import GraphState
from services.crm_history_service import crm_history_service

def retrieve_crm_node(state: GraphState) -> GraphState:
    """
    CRM Cache Retrieval Node
    메시지 생성 전, 동일 조건의 과거 성공 메시지가 있는지 확인합니다.
    
    Returns:
        Updated GraphState (preserves all existing keys)
    """
    print("\n" + "="*80)
    print("🧐 [Retrieve CRM Node] Checking Cache...")
    print("="*80)
    
    # [DEBUG] similar_user_ids 입력 확인
    similar_ids_input = state.get("similar_user_ids", [])
    print(f"🔍 [RETRIEVE_CRM DEBUG] similar_user_ids at entry: {len(similar_ids_input)} items")
    if similar_ids_input:
        print(f"   First 5: {similar_ids_input[:5]}")
    
    try:
        # 0. Check Reuse Option
        if not state.get("use_crm_cache", True):
            print("🚫 [Retrieve CRM] Reuse option is OFF. Skipping cache check.")
            state["cache_hit"] = False
            state["message_template"] = ""
            return state

        # 1. Prepare Arguments for Signature
        product_info = state["product_data"]
        user_data = state["user_data"]
        target_pid = state.get("target_persona", "1")
        channel = state.get("channel", "APP_PUSH")
        crm_reason = state.get("crm_reason", "regular")
        weather_detail = state.get("weather_detail", "")
        
        # [Modified] Use Persona ID instead of Name for Cache Signature Strictness
        # Previously loaded name from DB, but now we save/retrieve by ID ("1", "2")
        pass

        # 2. Strict Beauty Profile
        beauty_profile = {
            "skin_type": getattr(user_data, "skin_type", []),
            "skin_concerns": getattr(user_data, "skin_concerns", []),
            "keywords": getattr(user_data, "keywords", []),
            "preferred_tone": getattr(user_data, "preferred_tone", "")
        }

        # 3. Check Cache
        cached_msg = crm_history_service.find_message(
            brand=product_info["brand"],
            persona=str(target_pid),
            intent=crm_reason,
            weather=weather_detail,
            product_name=product_info["name"],
            channel=channel,
            beauty_profile=beauty_profile
        )
        
        if cached_msg:
            print(f"✅ [Retrieve CRM] Cache Hit! Using cached template.")
            print(f"📝 Cached message preview: {cached_msg[:100]}...")
            
            # [Moved Logic] Personalize logic moved here
            final_msg = cached_msg
            
            # [NEW] Add Notice Prefix
            notice = "━━━━━━━━━━━━━━━━━━━━━━━━\n📢 **시스템 알림**: 과거 동일한 조건의 생성 이력이 있어, 저장된 메시지를 불러옵니다.\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n\n"
            final_msg = notice + final_msg
            
            # [FIX] Update state directly to preserve all keys (including similar_user_ids)
            state["cache_hit"] = True
            state["compliance_passed"] = True
            state["message_template"] = cached_msg
            state["message"] = final_msg
            
            # [DEBUG] similar_user_ids 출력 확인
            similar_ids_output = state.get("similar_user_ids", [])
            print(f"🔍 [RETRIEVE_CRM DEBUG] similar_user_ids before return (cache hit): {len(similar_ids_output)} items")
            if similar_ids_output:
                print(f"   First 5: {similar_ids_output[:5]}")
            
            return state

        else:
            print(f"❄️ [Retrieve CRM] Cache Miss. Proceeding to Writer.")
            state["cache_hit"] = False
            
            # [DEBUG] similar_user_ids 출력 확인
            similar_ids_output = state.get("similar_user_ids", [])
            print(f"🔍 [RETRIEVE_CRM DEBUG] similar_user_ids before return (cache miss): {len(similar_ids_output)} items")
            if similar_ids_output:
                print(f"   First 5: {similar_ids_output[:5]}")
            
            return state

    except Exception as e:
        print(f"❌❌❌ [CRITICAL ERROR] Exception in retrieve_crm: {e}")
        import traceback
        traceback.print_exc()
        state["cache_hit"] = False
        return state
    
    # This should never be reached
    state["cache_hit"] = False
    return state
