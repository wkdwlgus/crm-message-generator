import { create } from 'zustand';
import { PERSONA_DB } from '../data/PersonaData';
import { PERSONA_OPTIONS, type PersonaOptionSet } from '../data/personaOptions';
import { SKIN_TYPE_OPTIONS, SKIN_CONCERN_OPTIONS, TONE_OPTIONS, KEYWORD_OPTIONS } from '../data/schemaData';
import type { CustomerDB } from '../services/customerService';
import { LogService } from '../services/logService';

// 데이터 타입 정의
export interface SimulationData {
  skin_type: string[];
  skin_concerns: string[];
  preferred_tone: string;
  keywords: string[];
}

export type ChannelType = 'APP_PUSH' | 'SMS' | 'KAKAO' | 'EMAIL';

// 페르소나 타입 정의
export interface Persona {
  id: string;
  name: string;
  desc: string;
  tone: string;
  keywords: string[];
}

interface AppState {
  // 상태
  personas: Persona[];
  selectedPersonaId: string | null;
  simulationData: SimulationData;
  intention: string | null;
  isBrandTargeting: boolean;
  targetBrand: string;
  selectedChannel: ChannelType | null;
  isGenerating: boolean;
  generatedResult: string | null;
  activeOptions: PersonaOptionSet;
  customerList: CustomerDB[];
  selectedCustomer: CustomerDB | null;
  messageLogs: any[];
  loadLogs: (userId: string) => Promise<void>;
  season: string | null;
  weatherDetail: string | null;



  // 액션
  setPersonas: (list: Persona[]) => void;
  setSelectedPersonaId: (id: string | null) => void;
  setSimulationData: (data: Partial<SimulationData>) => void;
  setIntention: (val: string | null) => void;
  setBrandTargeting: (val: boolean) => void;
  setTargetBrand: (brand: string) => void;
  setSelectedChannel: (channel: ChannelType | null) => void;
  setIsGenerating: (val: boolean) => void;
  setGeneratedResult: (result: string | null) => void;
  setCustomerList: (list: CustomerDB[]) => void;
  setSelectedCustomer: (customer: CustomerDB | null) => void;
  setSeason: (season: string | null) => void;
  setWeatherDetail: (detail: string | null) => void;

  // 기능 액션
  resetAll: () => void;
  selectPersona: (id: string | null) => void;
}

// 초기값 상수화
const INITIAL_SIMULATION_DATA: SimulationData = {
  skin_type: [],
  skin_concerns: [],
  preferred_tone: "Warm",
  keywords: [],
};

function buildDefaultOptions(): PersonaOptionSet {
  return {
    skinTypes: Object.keys(SKIN_TYPE_OPTIONS),
    concerns: Object.keys(SKIN_CONCERN_OPTIONS),
    tone: Object.keys(TONE_OPTIONS),
    keywords: Object.keys(KEYWORD_OPTIONS),
  };
}

export const useAppStore = create<AppState>((set, get) => ({
  personas: Object.values(PERSONA_DB).map((p) => ({
    ...p,
    keywords: [...p.keywords],
  })),
  selectedPersonaId: null,
  simulationData: { ...INITIAL_SIMULATION_DATA },
  intention: null,
  isBrandTargeting: false,
  targetBrand: '',
  selectedChannel: null,
  isGenerating: false,
  generatedResult: null,
  activeOptions: buildDefaultOptions(),
  customerList: [],
  selectedCustomer: null,
  messageLogs: [],
  loadLogs: async (userId: string) => {
    try {
      const logs = await LogService.getLogsByUser(userId);
      set({ messageLogs: logs });
    } catch (error) {
      console.error("Failed to load logs:", error);
    }
  },
  season: null,
  weatherDetail: null,
 
  // 액션 구현
  setSeason: (season) => set({ season, weatherDetail: null }),
  setWeatherDetail: (detail) => set({ weatherDetail: detail }),
  setPersonas: (list) => set({ personas: list }),
  setSelectedPersonaId: (id) => set({ selectedPersonaId: id }),
  setSimulationData: (newData) =>
    set((state) => ({
      simulationData: { ...state.simulationData, ...newData },
    })),
  setIntention: (val) => set({ intention: val }),
  setBrandTargeting: (val) => set({ isBrandTargeting: val }),
  setTargetBrand: (brand) => set({ targetBrand: brand }),
  setSelectedChannel: (channel) => set({ selectedChannel: channel }),
  setIsGenerating: (val) => set({ isGenerating: val }),
  setGeneratedResult: (result) => set({ generatedResult: result }),
  setCustomerList: (list) => set({ customerList: list }),
  setSelectedCustomer: (customer) =>
    set((state) => {
      if (!customer) {
        return {
          selectedCustomer: null,
          selectedPersonaId: null,
          activeOptions: buildDefaultOptions(),
          simulationData: { ...INITIAL_SIMULATION_DATA },
        };
      }

      const allowed: PersonaOptionSet = {
        skinTypes: customer.skin_type ?? [],
        concerns: customer.skin_concerns ?? [],
        tone: Object.keys(TONE_OPTIONS),
        keywords: customer.keywords ?? [],
    };

      return {
        selectedCustomer: customer,
        selectedPersonaId: customer.persona_category?.id ?? null,
        activeOptions: allowed,
        simulationData: { ...INITIAL_SIMULATION_DATA },
    };
  }),

  // ✅ 리셋 기능 (고객도 같이 리셋)
  resetAll: () =>
    set({
      selectedPersonaId: null,
      selectedCustomer: null,
      customerList: [], // 필요 없으면 제거 가능
      activeOptions: buildDefaultOptions(),
      simulationData: { ...INITIAL_SIMULATION_DATA },
      intention: null,
      isBrandTargeting: false,
      targetBrand: '',
      selectedChannel: null,
      isGenerating: false,
      generatedResult: null,
    }),
  // ✅ 페르소나 선택 시 활성 옵션 및 시뮬레이션 데이터 초기화
  selectPersona: (id) => {
    if (!id) {
      set({
        selectedPersonaId: null,
        activeOptions: buildDefaultOptions(),
        simulationData: { ...INITIAL_SIMULATION_DATA },
      });

      const customer = get().selectedCustomer;
      if (customer) {
        get().setSelectedCustomer(customer);
      }
      return;
    }

    const allowed = PERSONA_OPTIONS[id] ?? buildDefaultOptions();

    set({
      selectedPersonaId: id,
      activeOptions: allowed,
      simulationData: { ...INITIAL_SIMULATION_DATA },
    });

    // ✅ 고객이 선택돼 있으면 초기화 후 다시 고객값 주입
    const customer = get().selectedCustomer;
    if (customer) {
      get().setSelectedCustomer(customer);
    }
  },
}));