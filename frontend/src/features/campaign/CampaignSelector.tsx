import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { BRAND_LIST } from '../../data/schemaData'; 

// 작성 의도 옵션 정의
const INTENTIONS = [
  { 
    id: 'PROMOTION', 
    label: '📢 일반 홍보', 
    desc: '정기적인 소식지나 일반적인 앱 푸시를 보낼 때 사용합니다.' 
  },
  { 
    id: 'EVENT', 
    label: '🎉 이벤트/할인', 
    desc: '특정 기간 할인이나 프로모션 정보를 강조할 때 유리합니다.' 
  },
  { 
    id: 'WEATHER', 
    label: '☀️ 날씨/시즌', 
    desc: '현재 날씨나 계절감에 맞춰 감성적인 메시지를 작성합니다.' 
  },
];

export function CampaignSelector() {
  // 스토어에서 상태와 액션 가져오기 (변수명 최신화)
  const { 
    intention, setIntention, 
    isBrandTargeting, setBrandTargeting, 
    targetBrand, setTargetBrand 
  } = useAppStore();
  
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <section className="mb-10">
      <h2 className="font-black text-2xl mb-6 border-b-4 border-black inline-block italic pr-4">
        1. CAMPAIGN CONTEXT
      </h2>

      {/* 메인 컨테이너 box */}
      <div className="p-6 border-2 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        
        {/* 1) 작성 의도 선택 */}
        <div className="mb-8">
          <label className="block text-xs font-black uppercase mb-3 tracking-wider">
            WRITING INTENTION (작성 의도)
          </label>
          <div className="flex flex-col md:flex-row gap-4">
            {INTENTIONS.map((item) => (
              <div key={item.id} className="relative flex-1 group">
                <button
                  onClick={() => setIntention(item.id)}
                  onMouseEnter={() => setHoveredId(item.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  className={`
                    w-full py-4 px-2 font-black text-sm border-2 border-black transition-all duration-200
                    ${intention === item.id 
                      ? 'bg-yellow-300 shadow-none translate-x-[2px] translate-y-[2px]' // 선택됨
                      : 'bg-white hover:bg-gray-50 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' // 기본
                    }
                  `}
                >
                  {item.label}
                </button>

                {/* 툴팁 (Hover 시 등장) */}
                {hoveredId === item.id && (
                  <div className="absolute top-full mt-3 left-0 w-full z-20 bg-black text-white text-xs p-3 rounded-none animate-fadeIn shadow-xl">
                    <p>{item.desc}</p>
                    {/* 말풍선 꼬리 */}
                    <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-black rotate-45"></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 구분선 */}
        <hr className="border-black border-dashed mb-8 opacity-20" />

        {/* 2) 브랜드 타겟팅 여부 + 드롭다운 */}
        <div className="space-y-4">
          <div className={`
            flex items-center justify-between p-4 border-2 border-black transition-colors duration-300
            ${isBrandTargeting ? 'bg-blue-50' : 'bg-gray-50'}
          `}>
            <div>
              <span className="font-black text-sm block uppercase">TARGET SPECIFIC BRAND?</span>
              <span className="text-xs text-gray-600 font-medium mt-1 block">
                특정 브랜드의 톤앤매너와 정보를 반영합니다.
              </span>
            </div>
            
            <button
              onClick={() => setBrandTargeting(!isBrandTargeting)}
              className={`
                w-16 h-8 rounded-full border-2 border-black flex items-center px-1 transition-all duration-300
                ${isBrandTargeting ? 'bg-green-400 justify-end' : 'bg-gray-200 justify-start'}
              `}
            >
              {/* 토글 스위치 알맹이 */}
              <div className="w-5 h-5 bg-white border-2 border-black rounded-full shadow-sm"></div>
            </button>
          </div>

          {/* 토글 ON 시 나타나는 브랜드 선택 드롭다운 */}
          {isBrandTargeting && (
            <div className="animate-fadeIn p-4 border-2 border-black border-t-0 bg-blue-50/50 -mt-4 pt-6">
              <label className="block text-xs font-bold mb-2 text-blue-800">📌 SELECT BRAND</label>
              <select
                value={targetBrand}
                onChange={(e) => setTargetBrand(e.target.value)}
                className="w-full p-3 font-bold border-2 border-black bg-white text-black focus:outline-none focus:bg-yellow-50 focus:ring-2 focus:ring-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
              >
                <option value="">-- 브랜드를 선택해주세요 (Total 26) --</option>
                {BRAND_LIST.map((brand) => (
                  <option key={brand} value={brand}>{brand}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}