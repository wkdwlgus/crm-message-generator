import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { BRAND_LIST } from '../../data/schemaData'; 
import { ChannelSelector } from '../channel/ChannelSelector';

// 1. 작성 의도 옵션
const INTENTIONS = [
  { 
    id: 'PROMOTION', 
    label: '📢 일반 홍보', 
    desc: '정기적인 소식지나 일반적인 앱 푸시를 보낼 때 사용합니다.' 
  },
  { 
    id: 'EVENT', 
    label: '🎉 이벤트/할인', 
    desc: '최대 할인 제품 추천 등 프로모션 정보를 강조합니다.' 
  },
  { 
    id: 'WEATHER', 
    label: '☀️ 날씨/시즌', 
    desc: '계절과 날씨 이슈(미세먼지, 장마 등)에 맞춘 감성 메시지입니다.' 
  },
];

// 2. [NEW] 시즌 및 날씨 상세 데이터 정의
const SEASON_DATA = {
  SPRING: { 
    label: '🌸 봄', 
    details: ['미세먼지', '황사', '꽃가루'] 
  },
  SUMMER: { 
    label: '🍉 여름', 
    details: ['폭염', '자외선', '장마(습도)'] 
  },
  AUTUMN: { 
    label: '🍂 가을', 
    details: ['큰 일교차', '건조한 대기'] 
  },
  WINTER: { 
    label: '☃️ 겨울', 
    details: ['한파', '건조'] 
  },
};

type SeasonKey = keyof typeof SEASON_DATA;

export function CampaignSelector() {
  const { 
    intention, setIntention, 
    isBrandTargeting, setBrandTargeting, 
    targetBrand, setTargetBrand,
    // [NEW] 스토어에서 가져오기
    season, setSeason,
    weatherDetail, setWeatherDetail
  } = useAppStore();
  
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  // 의도 변경 핸들러 (WEATHER 아닐 때 시즌 정보 초기화는 선택사항이나, UX상 유지해도 무방)
  const handleIntentionChange = (id: string) => {
    if (intention === id) {
      setIntention(null);
    } else {
      setIntention(id);
      // 의도가 바뀌면 시즌 선택 초기화하고 싶다면 아래 주석 해제
      // if (id !== 'WEATHER') { setSeason(null); setWeatherDetail(null); }
    }
  };

  return (
    <section className="mb-10">
      <h2 className="font-black text-2xl mb-6 border-b-4 border-black inline-block italic pr-4">
        1. CAMPAIGN CONTEXT
      </h2>

      {/* 메인 컨테이너 box */}
      <div className="p-6 border-2 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        
        {/* A. 작성 의도 선택 */}
        <div className="mb-8">
          <label className="block text-xs font-black uppercase mb-3 tracking-wider">
            A. WRITING INTENTION (작성 의도)
          </label>
          <div className="flex flex-col md:flex-row gap-4">
            {INTENTIONS.map((item) => (
              <div key={item.id} className="relative flex-1 group">
                <button
                  onClick={() => handleIntentionChange(item.id)}
                  onMouseEnter={() => setHoveredId(item.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  className={`
                    w-full py-4 px-2 font-black text-sm border-2 border-black transition-all duration-200
                    ${intention === item.id 
                      ? 'bg-yellow-300 shadow-none translate-x-[2px] translate-y-[2px]' 
                      : 'bg-white hover:bg-gray-50 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'
                    }
                  `}
                >
                  {item.label}
                </button>

                {/* 툴팁 */}
                {hoveredId === item.id && (
                  <div className="absolute top-full mt-3 left-0 w-full z-20 bg-black text-white text-xs p-3 animate-fadeIn shadow-xl pointer-events-none">
                    <p>{item.desc}</p>
                    <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-black rotate-45"></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* B. [NEW] 날씨/시즌 선택 영역 (Weather 선택 시에만 등장) */}
        {intention === 'WEATHER' && (
          <div className="animate-in fade-in slide-in-from-top-2 duration-300 mb-8 p-5 bg-yellow-50 border-2 border-black border-dashed">
            <h3 className="text-xs font-black uppercase mb-4 text-yellow-800 flex items-center gap-2">
              <span>☀️ SEASONAL CONTEXT SETUP</span>
            </h3>

            {/* Step 1: 계절 선택 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              {Object.keys(SEASON_DATA).map((key) => (
                <button
                  key={key}
                  onClick={() => setSeason(key)}
                  className={`
                    py-2 text-sm font-bold border-2 border-black transition-all
                    ${season === key 
                      ? 'bg-black text-white' 
                      : 'bg-white text-gray-500 hover:text-black'
                    }
                  `}
                >
                  {SEASON_DATA[key as SeasonKey].label}
                </button>
              ))}
            </div>

            {/* Step 2: 상세 날씨 선택 (계절 선택 후 등장) */}
            {season && (
              <div className="animate-in fade-in duration-300">
                 <p className="text-[10px] font-bold text-gray-500 mb-2 uppercase">Detail Condition</p>
                 <div className="flex flex-wrap gap-2">
                   {SEASON_DATA[season as SeasonKey].details.map((detail) => (
                     <button
                       key={detail}
                       onClick={() => setWeatherDetail(weatherDetail === detail ? null : detail)}
                       className={`
                         px-3 py-1.5 text-xs font-bold border-2 border-black rounded-full transition-all shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]
                         ${weatherDetail === detail 
                           ? 'bg-blue-500 text-white border-black active:translate-x-[1px] active:translate-y-[1px] active:shadow-none' 
                           : 'bg-white hover:bg-blue-50 active:translate-x-[1px] active:translate-y-[1px] active:shadow-none'
                         }
                       `}
                     >
                       {detail}
                     </button>
                   ))}
                 </div>
              </div>
            )}
          </div>
        )}

        {/* 구분선 */}
        <hr className="border-black border-dashed mb-8 opacity-20" />

        {/* C. 브랜드 타겟팅 */}
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
              <div className="w-5 h-5 bg-white border-2 border-black rounded-full shadow-sm"></div>
            </button>
          </div>

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
      {/* 구분선 */}
      <hr className="border-black border-dashed mb-8 opacity-20" />

      {/* D. 채널 선택 (Campaign 카드 안으로 임베드) */}
      <ChannelSelector embedded />
      </div>
    </section>
  );
}