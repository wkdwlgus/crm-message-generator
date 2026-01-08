import { supabase } from '../lib/supabaseClient';

export interface MessageLog {
  user_id: string;
  channel: string;
  intention: string;
  content: string;
  beauty_profile: any;
}

export const LogService = {
  /**
   * 생성된 메시지 결과를 Supabase에 저장합니다.
   */
  async saveLog(logData: MessageLog) {
    console.log("📝 Saving generation log...", logData);

    const { data, error } = await supabase
      .from('message_logs')
      .insert([
        {
          user_id: logData.user_id,
          channel: logData.channel,
          intention: logData.intention,
          content: logData.content,
          beauty_profile: logData.beauty_profile,
          status: 'CREATED'
        }
      ])
      .select();

    if (error) {
      console.error("❌ Failed to save log:", error);
      // 로그 저장이 실패했다고 해서 사용자에게 에러를 띄울 필요는 없음 (조용히 실패)
    } else {
      console.log("✅ Log saved successfully:", data);
    }
  },

  /**
   * (수정됨) 특정 페르소나에 해당하는 시스템 히스토리(crm_message_history)를 가져옵니다.
   * 프론트엔드 저장이 중단되었으므로, 백엔드에서 저장한 내역을 보여줍니다.
   * @param personaId - 페르소나 ID (e.g., "1", "2")
   */
  async getLogsByUser(personaId: string) {
    let query = supabase
      .from('crm_message_history')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(20);

    // personaId가 있으면 필터링 ("1", "2" 등)
    // 단, "P1" 처럼 들어올 수 있으므로 숫자만 남기거나 확인 필요
    // 현재 프론트엔드는 "1", "2"로 관리됨 (PersonaData.ts 참조)
    if (personaId) {
      // 혹시 "P1" 등이 들어오면 "1"로 변환
      const cleanId = personaId.replace("P", "");
      if (cleanId) {
         query = query.eq('persona', cleanId);
      }
    }

    const { data, error } = await query;

    if (error) {
      console.error("❌ Failed to load CRM history:", error);
      return [];
    }
    
    // UI 포맷에 맞게 매핑
    return (data || []).map(row => ({
      id: row.id,
      user_id: row.persona, // user_id 대신 페르소나 Key 표시
      channel: row.channel || 'SMS',
      intention: row.intent,
      content: row.message_content,
      beauty_profile: row.beauty_profile,
      created_at: row.created_at
    }));
  }
};