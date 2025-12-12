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
  success: boolean;
  data: GeneratedMessage;
}

export interface ErrorResponse {
  success: boolean;
  error: string;
  retry_count?: number;
}

export type ChannelType = 'SMS' | 'KAKAO' | 'EMAIL';
