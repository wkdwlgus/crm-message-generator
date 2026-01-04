import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { PERSONA_DB } from '../../data/personaData';

export function StickySummary() {
  const { 
    intention, setIntention,
    selectedPersonaId, setSelectedPersonaId,
    setSimulationData,
    isBrandTargeting, setBrandTargeting, setTargetBrand, targetBrand,
    selectedChannel, setSelectedChannel
  } = useAppStore();

  // [수정] persona_name -> name 으로 변경
  // selectedPersonaId가 DB의 키인지 확인 후 접근
  const currentPersona = PERSONA_DB[selectedPersonaId as keyof typeof PERSONA_DB];
  const personaName = currentPersona?.name || 'Unknown';

  // 진행률 계산
  const steps = [
    { label: 'Intention', done: !!intention },
    { label: 'Persona', done: !!selectedPersonaId },
    { label: 'Channel', done: !!selectedChannel },
  ];
  
  const completedCount = steps.filter(s => s.done).length;
  const progress = Math.round((completedCount / steps.length) * 100);

  // 초기화 핸들러
  const handleReset = () => {
    if(window.confirm('모든 설정을 초기화하시겠습니까?')) {
      setIntention('PROMOTION');
      setSelectedPersonaId('1');
      setBrandTargeting(false);
      setTargetBrand('');
      setSimulationData({
        skin_type: [],
        skin_concerns: [],
        preferred_tone: 'Neutral',
        keywords: []
      });
      setSelectedChannel(null);
    }
  };

  return (
    <div className="sticky top-6">
      <div className="p-4 border-2 border-black bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
        {/* 헤더 */}
        <div className="flex justify-between items-center mb-4 border-b-2 border-black border-dashed pb-2">
          <h3 className="font-black text-sm italic">STATUS CHECK</h3>
          <span className="text-xs font-black bg-black text-white px-2 py-0.5 rounded-none">
            {progress}%
          </span>
        </div>

        {/* 진행 상태 리스트 */}
        <ul className="space-y-3 mb-6">
          {steps.map((step, idx) => (
            <li key={idx} className="flex items-center justify-between text-sm">
              <span className={`font-bold transition-opacity ${step.done ? 'opacity-100 text-black' : 'opacity-30 text-gray-500'}`}>
                {idx + 1}. {step.label}
              </span>
              <span>
                {step.done ? '✅' : '⬜'}
              </span>
            </li>
          ))}
        </ul>

        {/* 요약 정보 */}
        <div className="bg-gray-50 p-3 border-2 border-black mb-4 text-xs space-y-2 font-medium">
           <div className="flex gap-2 items-center">
             <span>🎯</span> 
             <span className="font-bold truncate">{intention || '-'}</span>
             {isBrandTargeting && targetBrand && (
                 <span className="text-[10px] text-blue-600 font-bold mt-0.5">
                   + Brand: {targetBrand}
                 </span>
               )}
           </div>
           
           <div className="flex gap-2 items-start">
             <span>👤</span> 
             <div className="flex flex-col">
               {/* 여기에 정확한 이름이 나옵니다 */}
               <span className="font-bold">{personaName}</span>
             </div>
           </div>

           <div className="flex gap-2 items-center">
             <span>📡</span> 
             <span className={`font-bold ${selectedChannel ? 'text-black' : 'text-gray-400'}`}>
               {selectedChannel || 'Not Selected'}
             </span>
           </div>
        </div>

        <button 
          onClick={handleReset}
          className="w-full py-2 text-xs font-black text-red-600 bg-red-50 hover:bg-red-100 border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-[2px] active:translate-y-[2px] transition-all"
        >
          🗑️ RESET ALL
        </button>
      </div>
    </div>
  );
}