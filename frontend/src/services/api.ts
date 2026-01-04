import type { ChannelType, CustomerPersona } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// 생성 요청에 필요한 데이터 타입 정의
interface GenerateRequestParams {
  userId: string;
  channel: ChannelType;
  intention?: string;     // 작성 의도
  hasBrand?: boolean;     // 브랜드 유무
  beautyProfile?: Record<string, any>; // 상세 프로필
  userPrompt?: string;    // 사용자 추가 프롬프트
}

export class ApiService {
  /**
   * 1. 메시지 생성 (POST 전환 완료)
   */
  static async generateMessage(params: GenerateRequestParams): Promise<{ data: any }> {
    const { userId, channel, ...restParams } = params;

    // POST 요청: 모든 데이터를 Body에 담습니다.
    const response = await fetch(`${API_BASE_URL}/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        channel: channel,
        ...restParams // 의도, 브랜드, 프롬프트 등이 여기에 들어감
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || '메시지 생성에 실패했습니다.');
    }

    const result = await response.json();

    return {
      data: {
        content: result.message,
        channel: result.method as ChannelType,
        user_id: result.user,
        generated_at: new Date().toISOString(),
        // 백엔드에서 규제 검사 로그를 준다면 여기에 매핑 추가
        compliance_log: result.compliance_log || [], 
      }
    };
  }

  /**
   * 2. 고객 목록 조회
   */
  static async getCustomers(): Promise<CustomerPersona[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/customers`);
      if (!response.ok) throw new Error('고객 목록 로딩 실패');
      return await response.json();
    } catch (error) {
      console.error("API Error:", error);
      return [];
    }
  }
}