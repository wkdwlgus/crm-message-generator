import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import type { SimulationData } from '../../store/useAppStore'; 

import { 
  SKIN_TYPE_OPTIONS, 
  SKIN_CONCERN_OPTIONS, 
  TONE_OPTIONS, 
  KEYWORD_OPTIONS 
} from '../../data/schemaData';

const BeautyProfileSelector = () => {
  const { simulationData, setSimulationData } = useAppStore();

  // 스타일 정의 (컨테이너 스타일 제거됨)
  const labelStyle = "block text-xs font-black uppercase mb-2 tracking-wider text-gray-700";
  // Select Box 스타일
  const selectStyle = "w-full p-2.5 font-bold border-2 border-black bg-white focus:outline-none focus:bg-yellow-50 focus:ring-2 focus:ring-black shadow-sm transition-colors";
  // Multi-select Box 스타일 (스크롤 가능 영역)
  const multiSelectBoxStyle = "w-full p-2 border-2 border-black bg-white h-32 overflow-y-auto space-y-1 shadow-sm scrollbar-thin scrollbar-thumb-black scrollbar-track-gray-100";
  // 체크박스 항목 스타일
  const checkboxItemStyle = "flex items-center gap-2 cursor-pointer hover:bg-yellow-100 p-1.5 transition-colors select-none";

  // [Type Guard] 멀티 셀렉트가 가능한 키만 추출 (preferred_tone 제외)
  type MultiSelectField = keyof Pick<SimulationData, 'skin_type' | 'skin_concerns' | 'keywords'>;

  // 멀티 셀렉트 핸들러 (타입 안전성 확보)
  const handleMultiSelect = (field: MultiSelectField, value: string) => {
    // 이제 TypeScript는 simulationData[field]가 무조건 string[] 임을 압니다.
    const currentList = simulationData[field];
    
    const newList = currentList.includes(value)
      ? currentList.filter((item) => item !== value) // 제거
      : [...currentList, value]; // 추가
    
    setSimulationData({ [field]: newList });
  };

  return (
    <div className="h-full">
      {/* 4가지 스키마 설정 영역 Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
        
        {/* 1. Skin Type (Multi) */}
        <div>
          <label className={labelStyle}>Skin Type (Multi)</label>
          <div className={multiSelectBoxStyle}>
            {Object.entries(SKIN_TYPE_OPTIONS).map(([key, label]) => (
              <label key={key} className={checkboxItemStyle}>
                <input 
                  type="checkbox"
                  checked={simulationData.skin_type.includes(key)}
                  onChange={() => handleMultiSelect('skin_type', key)}
                  className="w-4 h-4 text-black border-2 border-black focus:ring-0 rounded-none checked:bg-black checked:hover:bg-black"
                />
                <span className="text-sm font-bold">{label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* 2. Skin Concerns (Multi) */}
        <div>
          <label className={labelStyle}>Skin Concerns (Multi)</label>
          <div className={multiSelectBoxStyle}>
            {Object.entries(SKIN_CONCERN_OPTIONS).map(([key, label]) => (
              <label key={key} className={checkboxItemStyle}>
                <input 
                  type="checkbox"
                  checked={simulationData.skin_concerns.includes(key)}
                  onChange={() => handleMultiSelect('skin_concerns', key)}
                  className="w-4 h-4 text-black border-2 border-black focus:ring-0 rounded-none checked:bg-black checked:hover:bg-black"
                />
                <span className="text-sm font-bold">{label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* 3. Preferred Tone (Single) */}
        <div>
          <label className={labelStyle}>Preferred Tone (Single)</label>
          <div className="relative">
            <select 
              value={simulationData.preferred_tone} 
              onChange={(e) => setSimulationData({ preferred_tone: e.target.value })}
              className={selectStyle}
            >
              {Object.entries(TONE_OPTIONS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* 4. Keywords (Multi) */}
        <div>
          <label className={labelStyle}>Target Keywords (Multi)</label>
          <div className={multiSelectBoxStyle}>
            {Object.entries(KEYWORD_OPTIONS).map(([key, label]) => (
              <label key={key} className={checkboxItemStyle}>
                <input 
                  type="checkbox"
                  checked={simulationData.keywords.includes(key)}
                  onChange={() => handleMultiSelect('keywords', key)}
                  className="w-4 h-4 text-black border-2 border-black focus:ring-0 rounded-none checked:bg-black checked:hover:bg-black"
                />
                <span className="text-sm font-bold">{label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BeautyProfileSelector;