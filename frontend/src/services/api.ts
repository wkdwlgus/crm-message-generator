/**
 * API Service
 * 백엔드 API 호출 서비스 (실제 DB 연동 버전)
 */
import type { MessageResponse, ChannelType, CustomerPersona } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiService {
  /**
   * 1. 개인화 메시지 생성 API 호출
   * @param userId - 고객 ID (헤더로 전달)
   * @param channel - 메시지 채널 
   * @returns 생성된 메시지 응답
   */
  static async generateMessage(
    userId: string,
    channel: ChannelType = 'SMS'
  ): Promise<{ data: any }> { 
    
    // 백엔드: GET /message (Query: channel, Header: x-user-id)
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
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || '메시지 생성에 실패했습니다.');
    }

    const result = await response.json();

    // Backend(Python): { message: "...", user: "...", method: "..." }
    // Frontend(React): { content: "...", user_id: "...", channel: "..." }
    return {
      data: {
        content: result.message,       // 내용 매핑
        channel: result.method as ChannelType, // 채널 매핑
        user_id: result.user,          // 유저 ID 매핑
        generated_at: new Date().toISOString(),
      }
    };
  }

  /**
   * 2. 고객 목록 조회 API 호출 
   * * @returns Supabase에서 가져온 고객 리스트
   */
  static async getCustomers(): Promise<CustomerPersona[]> {
    try {
      // 백엔드: GET /customer
      const response = await fetch(`${API_BASE_URL}/customers`);
      
      if (!response.ok) {
        throw new Error('고객 목록을 불러오지 못했습니다.');
      }

      return await response.json();
    } catch (error) {
      console.error("API Error (getCustomers):", error);
      return []; // 에러 발생 시 빈 배열 반환 (화면 깨짐 방지)
    }
  }

  /**
   * 3. Health Check API 호출
   * * @returns 서버 상태
   */
  static async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    const response = await fetch(`${API_BASE_URL}/`);
    
    if (!response.ok) {
      throw new Error('서버에 연결할 수 없습니다.');
    }

    return response.json();
  }
}
