import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { PERSONA_DB } from '../../data/personaData';

const PersonaGrid = () => {
  const { selectedPersonaId, setSelectedPersonaId } = useAppStore();
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  // 상위 컨테이너(App.tsx의 STEP 2 박스)에서 padding을 처리하므로, 여기서는 자체 padding을 줄입니다.
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Object.entries(PERSONA_DB).map(([id, persona]) => {
        const isSelected = id === selectedPersonaId;
        
        return (
          <button
            key={id}
            onClick={() => setSelectedPersonaId(id)}
            onMouseEnter={() => setHoveredId(id)}
            onMouseLeave={() => setHoveredId(null)}
            className={`
              relative p-5 text-left border-2 border-black transition-all duration-200 h-full flex flex-col
              ${isSelected 
                ? 'bg-yellow-300 translate-x-[2px] translate-y-[2px] shadow-none' // 선택됨: 노란색 + 눌림
                : 'bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:bg-white/80' // 기본: 흰색 + 그림자
              }
            `}
          >
            {/* 1. 페르소나 이름 */}
            <h3 className="text-lg font-black mb-1 uppercase italic tracking-tight leading-tight">
              {persona.name}
            </h3>
            
            {/* 2. 톤앤매너 */}
            <p className="text-xs font-bold text-gray-500 mb-3 border-b-2 border-black/10 pb-1 inline-block">
              {persona.tone}
            </p>

            {/* 3. 상세 설명 */}
            <p className="text-xs font-medium leading-relaxed mb-4 text-gray-800 flex-1 break-keep">
              {persona.desc}
            </p>

            {/* 4. 키워드 태그 */}
            <div className="flex flex-wrap gap-1 mt-auto pt-2">
              {persona.keywords.map((kw, idx) => (
                <span key={idx} className="text-[10px] font-bold border border-black px-1.5 py-0.5 bg-white whitespace-nowrap">
                  #{kw}
                </span>
              ))}
            </div>
          </button>
        );
      })}
    </div>
  );
};

export default PersonaGrid;