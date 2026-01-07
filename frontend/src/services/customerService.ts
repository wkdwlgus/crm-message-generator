import { supabase } from '../lib/supabaseClient';
import { 
  SKIN_TYPE_OPTIONS, 
  SKIN_CONCERN_OPTIONS, 
  TONE_OPTIONS, 
  KEYWORD_OPTIONS 
} from '../data/schemaData';

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

    // DB 컬럼(_fixed 버전) -> Frontend Interface 매핑
    const mappedData = (data || []).map((row: any) => ({
      ...row,
      // 1. Text -> String[] (UI는 멀티 셀렉트지만 DB는 단일 텍스트)
      skin_type: row.skin_type_fixed || [],

      // 2. Text[] -> String[] (그대로 사용)
      skin_concerns: row.skin_concerns_fixed || [],

      // 3. Text[] -> String (UI는 단일 셀렉트지만 DB는 배열)
      preferred_tone: row.preferred_tone_fixed?.[0] || '',

      // 4. Text -> String[] (UI는 멀티 셀렉트지만 DB는 단일 텍스트)
      keywords: row.keywords_fixed || [],
    }));

    return mappedData;
  },

  /**
   * [UPDATE] 고객의 뷰티 프로필 정보 업데이트
   * - Generate 버튼 누를 때 실행됨
   * - 화면에 있는 SimulationData 값을 DB 컬럼에 맵핑해서 저장
   */
  async updateCustomerProfile(userId: string, profileData: any) {
    console.log(`💾 Saving profile for ${userId}...`, profileData);

    // [한글 변환 헬퍼 함수]
    const toKoreanList = (list: string[], map: Record<string, string>) => {
      if (!list) return [];
      return list.map(item => map[item] || item);
    };

    const toKoreanOne = (item: string, map: Record<string, string>) => {
      if (!item) return null;
      return map[item] || item;
    };

    // SimulationData(Store) -> DB Column 매핑
    // skin_type_fixed 등은 불변(읽기 전용)이므로 수정하지 않고,
    // 원본 컬럼(skin_type 등)에 한글로 변환하여 저장합니다.
    const updates = {
      // 1. Skin Type (DB: text[]) -> ["건성"]
      skin_type: toKoreanList(profileData.skin_type, SKIN_TYPE_OPTIONS),

      // 2. Skin Concerns (DB: text[]) -> ["트러블", "모공"]
      skin_concerns: toKoreanList(profileData.skin_concerns, SKIN_CONCERN_OPTIONS),

      // 3. Preferred Tone (DB: text) -> "웜톤" (단일 문자열)
      preferred_tone: toKoreanOne(profileData.preferred_tone, TONE_OPTIONS),

      // 4. Keywords (DB: text[]) -> ["비건", "할인"]
      keywords: toKoreanList(profileData.keywords, KEYWORD_OPTIONS),
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