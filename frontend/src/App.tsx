import { CampaignSelector } from './features/campaign/CampaignSelector';
import PersonaGrid from './features/persona/PersonaGrid'; 

// [수정 포인트] 중괄호 { }를 제거했습니다. (default export를 불러오기 위함)
import BeautyProfileSelector from './features/beautyprofile/BeautyProfileSelector'; 

import { ChannelSelector } from './features/channel/ChannelSelector'; 
import { StickySummary } from './features/shared/StickySummary';

function App() {
  return (
    <div className="min-h-screen bg-[#f8f9fa] p-8 font-sans text-gray-900">
      {/* 헤더 */}
      <header className="max-w-6xl mx-auto mb-10 flex items-center gap-4">
        <div className="w-12 h-12 bg-black text-white flex items-center justify-center font-black text-2xl shadow-[4px_4px_0px_0px_rgba(0,0,0,0.2)]">
          D
        </div>
        <div>
          <h1 className="text-2xl font-black tracking-tighter">DAPANDA</h1>
          <p className="text-xs tracking-widest opacity-60">CRM MESSAGE GENERATOR v2.0</p>
        </div>
      </header>

      {/* 메인 레이아웃 */}
      <main className="max-w-6xl mx-auto grid grid-cols-12 gap-8">
        
        {/* 왼쪽: 설정 패널 */}
        <div className="col-span-8 flex flex-col gap-10">
          
          {/* 1. 캠페인 설정 */}
          <CampaignSelector />

          {/* 2. 타겟 페르소나 & 스키마 설정 (통합됨) */}
          <section>
            <h2 className="font-black text-2xl mb-6 border-b-4 border-black inline-block italic pr-4">
              2. TARGET PERSONA & BEAUTY PROFILE
            </h2>
            
            {/* 큰 컨테이너 박스 */}
            <div className="border-2 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
              
              {/* A. 페르소나 선택 영역 */}
              <div className="p-6 bg-gray-50 border-b-2 border-black border-dashed">
                <h3 className="font-black text-sm uppercase mb-4 text-gray-500">
                  A. SELECT PERSONA (페르소나 선택)
                </h3>
                <PersonaGrid />
              </div>

              {/* B. 스키마 수정 영역 */}
              <div className="p-6">
                <h3 className="font-black text-sm uppercase mb-4 text-gray-500">
                  B. EDIT SCHEMA (세부 속성 수정)
                </h3>
                <BeautyProfileSelector />
              </div>

            </div>
          </section>

          {/* 3. 채널 선택 */}
          <ChannelSelector />

        </div>

        {/* 오른쪽: 스티키 요약 & 결과 */}
        <div className="col-span-4 h-full relative">
          <div className="sticky top-8">
             <StickySummary />
          </div>
        </div>

      </main>
    </div>
  );
}

export default App;