import { CampaignSelector } from './features/campaign/CampaignSelector';
import PersonaGrid from './features/persona/PersonaGrid';
import { CustomerDashboard } from './features/dashboard/CustomerDashboard';
import { ChannelSelector } from './features/channel/ChannelSelector';
import { StickySummary } from './features/shared/StickySummary';

function App() {
  return (
    <div className="min-h-screen bg-[#f8f9fa] p-8 font-sans text-gray-900">
      {/* Header */}
      <header className="max-w-6xl mx-auto mb-12">
        <div className="inline-block bg-black px-5 py-4 rounded-sm">
          <h1 className="text-2xl font-extrabold tracking-tight text-white leading-none">
            DAPANDA
          </h1>
          <p className="mt-1 text-[11px] tracking-widest text-white/60 leading-none">
            CRM MESSAGE GENERATOR FOR BEAUTY BRANDS
          </p>
        </div>
      </header>

      {/* 메인 레이아웃 */}
      <main className="max-w-6xl mx-auto grid grid-cols-12 gap-8">
        {/* 왼쪽: 설정 패널 (8칸) */}
        <div className="col-span-8 flex flex-col gap-10">
          {/* 1. 캠페인 설정 */}
          <CampaignSelector />

          {/* 2. 타겟 페르소나 & 대시보드 */}
          <section>
            <h2 className="font-black text-2xl mb-6 border-b-4 border-black inline-block italic pr-4">
              2. TARGET PERSONA & DETAILS
            </h2>

            {/* 큰 컨테이너 박스 */}
            <div className="border-2 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
              {/* A. 페르소나 선택 영역 */}
              <div className="p-6 bg-gray-50 border-b-2 border-black border-dashed">
                <h3 className="font-black text-sm uppercase mb-4 text-gray-500">
                  A. SELECT PERSONA
                </h3>
                <PersonaGrid />
              </div>

              {/* B. 대시보드 (프로필 수정 + 히스토리) */}
              <div className="p-6">
                <h3 className="font-black text-sm uppercase mb-4 text-gray-500">
                  B. DETAILED SETTINGS & HISTORY
                </h3>

                {/* 여기가 교체된 부분입니다 */}
                <CustomerDashboard />
              </div>
            </div>
          </section>

          {/* 3. 채널 선택 */}
          <ChannelSelector />
        </div>

        {/* 오른쪽: 스티키 요약 & 결과 (4칸) */}
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