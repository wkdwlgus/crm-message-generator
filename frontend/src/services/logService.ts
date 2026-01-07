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
   * (추후 사용) 특정 유저의 생성 이력 가져오기
   */
  async getLogsByUser(userId: string) {
    const { data, error } = await supabase
      .from('message_logs')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    return data || [];
  }
};