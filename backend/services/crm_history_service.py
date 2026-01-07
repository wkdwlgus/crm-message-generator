from typing import Optional, Dict, List, Any
import hashlib
import json
from supabase import create_client, Client
from config import settings
from datetime import datetime
from zoneinfo import ZoneInfo

class CRMHistoryService:
    def __init__(self):
        self.sb: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.table_name = "crm_message_history"

    def _generate_signature(self, brand: str, persona: str, intent: str, weather: str, product_name: str, channel: str, beauty_profile: Dict) -> str:
        """
        검색 조건을 기반으로 고유 서명 생성 (Exact Match용)
        product_name 및 beauty_profile 4대 요소(tone, type, concerns, keywords) 기준
        [NEW] channel 추가
        """
        # 주요 프로필 요소만 추출하여 서명 생성 (Strict Match)
        profile_key = {
            "skin_type": sorted(beauty_profile.get("skin_type", [])),
            "skin_concerns": sorted(beauty_profile.get("skin_concerns", [])),
            "keywords": sorted(beauty_profile.get("keywords", [])),
            "tone": beauty_profile.get("preferred_tone", "")
        }
        
        # product_name, channel 포함해서 해시 생성
        raw_str = f"{brand}|{persona}|{intent}|{weather}|{product_name}|{channel}|{json.dumps(profile_key, sort_keys=True)}"
        return hashlib.sha256(raw_str.encode()).hexdigest()

    def find_message(self, 
                     brand: str, 
                     persona: str, 
                     intent: str, 
                     weather: str, 
                     product_name: str,
                     channel: str,
                     beauty_profile: Dict) -> Optional[str]:
        """
        조건에 맞는 메시지 검색
        """
        signature = self._generate_signature(brand, persona, intent, weather, product_name, channel, beauty_profile)
        
        try:
            # signature로 검색
            resp = (
                self.sb.table(self.table_name)
                .select("message_content")
                .eq("query_signature", signature)
                .limit(1)
                .execute()
            )
            
            if resp.data and len(resp.data) > 0:
                print(f"✅ [CRM Cache] Hit! (sig={signature[:8]}...)")
                return resp.data[0]["message_content"]
            else:
                print(f"💨 [CRM Cache] Miss (sig={signature[:8]}...)")
                return None
                
        except Exception as e:
            print(f"⚠️ [CRM Cache] Error finding message: {e}")
            return None

    def save_message(self, 
                     brand: str, 
                     persona: str, 
                     intent: str, 
                     weather: str, 
                     product_name: str,
                     channel: str,
                     beauty_profile: Dict, 
                     message_content: str):
        """
        생성된 메시지 저장
        """
        signature = self._generate_signature(brand, persona, intent, weather, product_name, channel, beauty_profile)
        
        payload = {
            "brand": brand,
            "persona": persona,
            "intent": intent,
            "weather": weather,
            # "product_name": product_name, # DB Column 없음
            "channel": channel,
            "beauty_profile": beauty_profile,
            "message_content": message_content,
            "query_signature": signature,
            "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
        }
        
        try:
            self.sb.table(self.table_name).insert(payload).execute()
            print(f"💾 [CRM Cache] Saved new message (sig={signature[:8]}...)")
        except Exception as e:
            print(f"⚠️ [CRM Cache] Failed to save message: {e}")

# Singleton Instance
crm_history_service = CRMHistoryService()
