/**
 * API Service
 * 백엔드 API 호출 서비스
 */
import type { MessageResponse, ChannelType } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiService {
  /**
   * 개인화 메시지 생성 API 호출
   * 
   * @param userId - 고객 ID
   * @param channel - 메시지 채널 (SMS, KAKAO, EMAIL)
   * @returns 생성된 메시지 응답
   */
  static async generateMessage(
    userId: string,
    channel: ChannelType = 'SMS'
  ): Promise<MessageResponse> {
    const response = await fetch(
      `${API_BASE_URL}/message?channel=${channel}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': userId,
        },
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '메시지 생성에 실패했습니다.');
    }

    return response.json();
  }

  /**
   * Health Check API 호출
   * 
   * @returns 서버 상태
   */
  static async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    const response = await fetch(`${API_BASE_URL}/`);
    
    if (!response.ok) {
      throw new Error('서버에 연결할 수 없습니다.');
    }

    return response.json();
  }
}
