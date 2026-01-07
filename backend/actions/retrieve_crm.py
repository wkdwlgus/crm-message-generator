
import json
from actions.orchestrator import GraphState
from services.crm_history_service import crm_history_service

def retrieve_crm_node(state: GraphState) -> GraphState:
    """
    CRM Cache Retrieval Node
    메시지 생성 전, 동일 조건의 과거 성공 메시지가 있는지 확인합니다.
    """
    print("\n" + "="*80)
    print("🧐 [Retrieve CRM Node] Checking Cache...")
    print("="*80)
    
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
        
        # Persona Name Resolution (Optional for Signature, but good for consistency)
        # Signature uses 'persona' string. In saving we used name. Here we might need name too if signature depends on it.
        # Let's use the same logic as save/writer.
        # Note: If signature uses 'persona' as just the ID or generic, it's easier.
        # Previous logic used 'persona_name' from DB.
        # I need to duplicate the persona loading logic or rely on `target_persona` ID if I change the signature strategy.
        # Wait, previous `message_writer` loaded `persona_db`.
        # I should load it here too to match the signature.
        
        base_path = "backend/actions/persona_db.json" # Relative path might be tricky, let's use os
        import os
        base_path = os.path.dirname(os.path.dirname(__file__))
        persona_db_path = os.path.join(base_path, "actions/persona_db.json")
        try:
            with open(persona_db_path, "r", encoding="utf-8") as f:
                pdb = json.load(f)
                persona_name = pdb.get(str(target_pid), {}).get("persona_name", "Unknown")
        except:
            persona_name = "Unknown"

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
            persona=persona_name,
            intent=crm_reason,
            weather=weather_detail,
            product_name=product_info["name"],
            channel=channel,
            beauty_profile=beauty_profile
        )
        
        if cached_msg:
            print(f"✅ [Retrieve CRM] Cache Hit! Using cached template.")
            state["cache_hit"] = True
            state["message_template"] = cached_msg # Template loaded
            # message will be finalized in personalize node
        else:
            print(f"❄️ [Retrieve CRM] Cache Miss. Proceeding to Writer.")
            state["cache_hit"] = False
            state["message_template"] = ""

    except Exception as e:
        print(f"⚠️ [Retrieve CRM] Error checking cache: {e}")
        state["cache_hit"] = False
        
    return state
