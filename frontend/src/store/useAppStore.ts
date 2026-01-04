import { create } from 'zustand';

// 데이터 타입 정의
export interface SimulationData {
  skin_type: string[];
  skin_concerns: string[];
  preferred_tone: string;
  keywords: string[];
}

// 채널 타입 정의 (새로 추가됨)
export type ChannelType = 'APP_PUSH' | 'SMS' | 'KAKAO' | 'EMAIL';

interface AppState {
  selectedPersonaId: string;
  simulationData: SimulationData;
  intention: string;
  isBrandTargeting: boolean;
  targetBrand: string;
  
  // 채널 관련 상태 (새로 추가됨)
  selectedChannel: ChannelType | null;

  // Actions
  setSelectedPersonaId: (id: string) => void;
  setSimulationData: (data: Partial<SimulationData>) => void;
  setIntention: (val: string) => void;
  setBrandTargeting: (val: boolean) => void;
  setTargetBrand: (brand: string) => void;
  
  // 채널 선택 액션 (새로 추가됨)
  setSelectedChannel: (channel: ChannelType | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedPersonaId: '1',
  simulationData: {
    skin_type: [],
    skin_concerns: [],
    preferred_tone: 'Neutral',
    keywords: []
  },
  intention: 'PROMOTION',
  isBrandTargeting: false,
  targetBrand: '',
  
  // 초기값
  selectedChannel: null,

  setSelectedPersonaId: (id) => set({ selectedPersonaId: id }),
  setSimulationData: (newData) => set((state) => ({
    simulationData: { ...state.simulationData, ...newData }
  })),
  setIntention: (val) => set({ intention: val }),
  setBrandTargeting: (val) => set({ isBrandTargeting: val }),
  setTargetBrand: (brand) => set({ targetBrand: brand }),
  
  // 구현
  setSelectedChannel: (channel) => set({ selectedChannel: channel }),
}));