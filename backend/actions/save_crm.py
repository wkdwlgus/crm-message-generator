
import json
import os
from typing import Dict, Any
from actions.orchestrator import GraphState
from services.crm_history_service import crm_history_service

def save_crm_message_node(state: GraphState) -> GraphState:
    """
    CRM 메시지 저장 Node
    Compliance Check를 통과한 메시지를 CRM History에 영구 저장합니다.
    """
    print("\n" + "="*80)
    print("💾 [Save CRM Node] Started")
    print("="*80)
    
    try:
        # 1. 필요 데이터 추출
        product_info = state["product_data"]
        user_data = state["user_data"]
        target_pid = state.get("target_persona", "1")
        channel = state.get("channel", "APP_PUSH")
        
        # 2. Persona Name Resolution (DB Load)
        base_path = os.path.dirname(os.path.dirname(__file__))
        persona_db_path = os.path.join(base_path, "actions/persona_db.json")
        try:
            with open(persona_db_path, "r", encoding="utf-8") as f:
                pdb = json.load(f)
                persona_name = pdb.get(str(target_pid), {}).get("persona_name", "Unknown")
        except:
            persona_name = "Unknown"
            
        # 3. Construct Strict Beauty Profile (for Signature)
        beauty_profile = {
            "skin_type": getattr(user_data, "skin_type", []),
            "skin_concerns": getattr(user_data, "skin_concerns", []),
            "keywords": getattr(user_data, "keywords", []),
            "preferred_tone": getattr(user_data, "preferred_tone", "")
        }
        
        # 4. Determine Message Content (Template vs Final)
        # 템플릿이 있으면 템플릿을 저장(재사용성 확보), 없으면 최종 메시지 저장
        msg_content = state.get("message_template") or state["message"]
        
        # 5. Call Service to Save
        crm_history_service.save_message(
            brand=product_info["brand"],
            persona=persona_name,
            intent=state.get("crm_reason", "regular"),
            weather=state.get("weather_detail", ""),
            product_name=product_info["name"],
            channel=channel,
            beauty_profile=beauty_profile,
            message_content=msg_content
        )
        print("✅ Message successfully saved to CRM History.")
        
    except Exception as e:
        print(f"⚠️ Failed to save message history: {e}")
        # 저장이 실패해도 플로우는 계속 진행 (메시지 발송은 되어야 함)
        
    return state
