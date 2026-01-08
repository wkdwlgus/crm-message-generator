/**
 * API Types
 * 백엔드 API 응답 타입 정의
 */

export interface GeneratedMessage {
  user_id: string;
  message_content: string;
  channel: string;
  product_id: string;
  persona_id: string;
  generated_at?: string;
}

export interface MessageResponse {
  content: string;
  channel: ChannelType;
  generated_at?: string;
  user_id?: string;
  persona_id?: string;
  similar_user_ids?: string[];  // [NEW] 유사 유저 ID 리스트
}

export interface CustomerPersona {
  user_id: string;        // 핵심: 메시지 생성 시 보낼 ID
  name: string;           // 표시용: 이름
  membership_level: string; // 표시용: 뱃지 (예: GOLD)
  skin_type?: string[];    // 표시용: 태그 (배열이 아닐 경우를 대비해 ? 처리)
  keywords?: string[];     // 표시용: 태그
  preferred_tone?: string; // 표시용: 톤앤매너 설명
  persona_category?: string; // 표시용: 페르소나 카테고리
}

export interface ErrorResponse {
  success: boolean;
  error: string;
  retry_count?: number;
}

export type ChannelType = 'APP_PUSH' | 'SMS' | 'KAKAO' | 'EMAIL';
