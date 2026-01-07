import { supabase } from '../lib/supabaseClient';

interface PersonaCategory {
    id: string;
    desc: string;
    name: string;
    tone: string;
    keywords: string[];
}

// 1. Supabase 테이블 스키마 
export interface CustomerDB {
  user_id: string;    
  name: string; 
  skin_type: string[];
  skin_concerns: string[];
  preferred_tone: string;
  keywords: string[];
  persona_category: PersonaCategory;
}

export const CustomerService = {
  /**
   * [READ] 모든 고객 목록 가져오기
   */
  async getCustomers(): Promise<CustomerDB[]> {
    const { data, error } = await supabase
      .from('customers')
      .select('*')
      .order('user_id', { ascending: true }); // user_id 순 정렬

    if (error) {
      console.error('❌ Supabase Load Error:', error);
      throw error;
    }
    return data || [];
  },

  /**
   * [UPDATE] 고객의 뷰티 프로필 정보 업데이트
   * - Generate 버튼 누를 때 실행됨
   * - 화면에 있는 SimulationData 값을 DB 컬럼에 맵핑해서 저장
   */
  async updateCustomerProfile(userId: string, profileData: any) {
    console.log(`💾 Saving profile for ${userId}...`, profileData);

    // SimulationData(Store) -> DB Column 매핑
    const updates = {
      skin_type: profileData.skin_type,
      skin_concerns: profileData.skin_concerns,
      preferred_tone: profileData.preferred_tone ?? null,
      keywords: profileData.keywords,
      // name 등은 변경하지 않음
    };

    const { data, error } = await supabase
      .from('customers')
      .update(updates)       // 업데이트할 내용
      .eq('user_id', userId) // 조건: user_id가 같은 행
      .select();

    if (error) {
      console.error('❌ Supabase Update Error:', error);
      throw error;
    }
    
    if (!data || data.length === 0) {
      console.error(`⚠️ [Update Failed] DB에서 ID가 '${userId}'인 고객을 찾을 수 없습니다. (업데이트된 행: 0개)`);
      alert(`DB 업데이트 실패: ID '${userId}'가 존재하지 않습니다.`);
    } else {
      console.log(`✅ [Update Success] ID '${userId}' 정보 업데이트 완료:`, data);
    }
    
    return data;
  }
};