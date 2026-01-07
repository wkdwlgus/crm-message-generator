import type { ChannelType, CustomerPersona } from '../types/api';
import axios from 'axios';

// FastAPI 서버 주소
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface GenerateRequestParams {
  userId: string;
  channel: ChannelType;
  intention?: string | null;
  hasBrand?: boolean;
  targetBrand?: string | null;
  season?: string | null;         
  weatherDetail?: string | null;  
  beautyProfile?: Record<string, any>;
  userPrompt?: string;
  persona?: string;
}

export class ApiService {
  /**
   * 메시지 생성
   * - fetch → axios.post 로 변경
   * - 모든 데이터는 body에 JSON으로 전달
   */
  static async generateMessage(params: GenerateRequestParams
  ): Promise<{ data: any }> {

    try {
      const response = await axios.post(`${API_BASE_URL}/message`, {
        userId: params.userId,
        channel: params.channel,
        intention: params.intention,
        hasBrand: params.hasBrand,
        targetBrand: params.targetBrand,
        season: params.season,
        weatherDetail: params.weatherDetail,
        beautyProfile: params.beautyProfile,
        userPrompt: params.userPrompt,
        persona: params.persona,
      });

      return response.data;
} catch (error: any) {
  console.error("API Call Failed:", error);

  // ✅ 추가: 서버가 준 응답(422 detail) 찍기
  console.log("status:", error?.response?.status);
  console.log("response data:", error?.response?.data);
  console.log("response detail:", error?.response?.data?.detail);

  // ✅ 추가: 내가 실제로 서버에 보낸 body 확인
  console.log("sent params:", params);

  throw error;
  }
  }

  /**
   * 고객 목록 (아직 Mock)
   * → 추후 Supabase로 교체
   */
  static async getCustomers(): Promise<CustomerPersona[]> {
    return [];
  }
}

// Mock 함수 (백업용)
function mockGenerate(params: any) {
  return Promise.resolve({
    data: {
      message: 'This is a mock response',
      params,
    },
  });
}