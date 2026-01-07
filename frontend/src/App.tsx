import { useState, useEffect, useRef } from 'react';
import { UserIdInput } from './components/UserIdInput';
import { ChannelSelector } from './components/ChannelSelector';
import { MessageDisplay } from './components/MessageDisplay';
import { LoadingSpinner } from './components/LoadingSpinner';
import { ErrorMessage } from './components/ErrorMessage';
import { AddPersonaModal } from './components/AddPersonaModal';
import { ApiService } from './services/api';
import type { ChannelType, GeneratedMessage, CustomerPersona } from './types/api';
import './App.css';

function App() {
  // --- 1. State 정의 ---
  const [channel, setChannel] = useState<ChannelType | null>(null);
  const [loading, setLoading] = useState(false);
  
  // 3. Context Options (Demo용)
  const [brand, setBrand] = useState('이니스프리');
  const [reason, setReason] = useState('신제품 출시 이벤트');
  const [weatherDetail, setWeatherDetail] = useState('');

  // 고객 ID 및 데이터 관리 (실제 데이터 연동)
  const [userId, setUserId] = useState<string>('');
  const [customers, setCustomers] = useState<CustomerPersona[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerPersona | null>(null);
  const [customPersonas, setCustomPersonas] = useState<CustomerPersona[]>([]);
  
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<GeneratedMessage | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 참조(Ref) 정의
  const mainRef = useRef<HTMLDivElement | null>(null);

  // [Fix] 안전한 렌더링을 위한 헬퍼 함수
  const safeRender = (value: any, fallback = ''): string => {
    if (value === null || value === undefined) return fallback;
    if (typeof value === 'object') return JSON.stringify(value); // 객체라면 문자열로 변환
    return String(value);
  };

  // 생성 가능 여부 체크 (고객 ID와 채널이 있어야 함)
  const canGenerate = userId !== '' && channel !== null && !loading;

  // 화면에 보여줄 전체 리스트 (DB 데이터 + 사용자 추가 데이터)
  const allPersonas = [...customers, ...customPersonas];

  // 페르소나 추가 핸들러 (+ADD 버튼)
  const handleAddPersona = () => {
    // 임시 페르소나 데이터 생성 (껍데기만)
    const newId = `temp_${Date.now()}`; // 고유 ID 생성
    const newPersona: CustomerPersona = {
      user_id: newId,
      name: `New Persona ${customPersonas.length + 1}`,
      membership_level: 'TEMP',
      preferred_tone: '아직 설정되지 않음',
      persona_category: '아직 설정되지 않음',
      keywords: [],
      skin_type: []
    };
    
    setCustomPersonas((prev) => [...prev, newPersona]);
  };

  // 페르소나 삭제 핸들러 (쓰레기통 버튼)
  const handleDeletePersona = () => {
    if (!selectedCustomer) return;

    // P1~P5 (DB에서 온 데이터)인지 확인 -> 삭제 방지
    const isDefault = customers.some(c => c.user_id === selectedCustomer.user_id);
    
    if (isDefault) {
      alert("P1~P5 (기본 페르소나)는 삭제할 수 없습니다! 🔒");
      return;
    }

    // 삭제 실행 (목록에서 제거 & 선택 해제)
    if (window.confirm("선택한 페르소나를 삭제하시겠습니까?")) {
      setCustomPersonas(prev => prev.filter(p => p.user_id !== selectedCustomer.user_id));
      setSelectedCustomer(null);
      setUserId('');
    }
  };

  // --- 2. 초기 데이터 로딩 (useEffect) ---
  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const data = await ApiService.getCustomers();
        setCustomers(data);
      } catch (err) {
        console.error("고객 데이터 로딩 실패:", err);
        // 필요 시 에러 UI 처리 가능
      }
    };
    fetchCustomers();
  }, []);

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const data = await ApiService.getCustomers();
        // 데이터가 잘 왔는지 콘솔에서 확인
        console.log("✅ 백엔드에서 가져온 고객 목록:", data);
        setCustomers(data);
      } catch (err) {
        console.error("❌ 고객 데이터 로딩 실패:", err);
      }
    };
    fetchCustomers();
  }, []);

  // --- 3. 핸들러 로직 ---

  // 페르소나(고객) 버튼 클릭 핸들러
  const handlePersonaClick = (customer: CustomerPersona) => {
    // 이미 선택된 고객을 다시 누르면 선택 해제
    if (selectedCustomer?.user_id === customer.user_id) {
      setSelectedCustomer(null);
      setUserId('');
    } else {
      // 새로운 고객 선택
      setSelectedCustomer(customer);
      setUserId(customer.user_id); // 중요: ID 자동 설정
      setError(null); // 에러 초기화
      setMessage(null); // 이전 메시지 초기화
    }
  };

  // 메시지 생성(Generate) 버튼 핸들러
  const handleGenerateClick = async () => {
    if (!userId) {
      alert("고객 ID를 입력해주세요!");
      return;
    }
    if (!channel) {
      alert("메시지 채널을 선택해주세요!");
      return;
    }
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      // ApiService 호출
      // P1, P2... 라벨은 allPersonas의 인덱스로 추정 (P1 = index 0)
      const personaLabel = selectedCustomer 
        ? `P${allPersonas.findIndex(p => p.user_id === selectedCustomer.user_id) + 1}` 
        : 'P1';

      const response = await ApiService.generateMessage(userId, channel, {
        brand,
        reason,
        weather_detail: reason === '날씨' ? weatherDetail : undefined,
        persona: personaLabel
      });
      setMessage(response.data);
    } catch (err: any) {
      console.error(err);
      setError(err?.message || '메시지 생성 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

    // 모든 선택 상태를 초기화
  const handleReset = () => {
    setMessage(null);           // 결과 메시지 지우기
    setSelectedCustomer(null);  // 선택된 고객 해제
    setChannel(null);          // 선택된 채널 해제
    setBrand('이니스프리');    // 브랜드 초기화
    setReason('신제품 출시 이벤트'); // 이유 초기화
    setWeatherDetail('');      // 날씨 상세 초기화
  };

  // 고객은 유지하고 결과창만 닫음
  const handleNextMessage = () => {
    setMessage(null); // 결과 메시지만 지우면, 다시 생성 화면이 나옵니다.
  };

  // 외부 클릭 시 선택 해제 핸들러
  useEffect(() => {
    const handleOutside = (event: PointerEvent) => {
      const target = event.target as Node;
      
      // 메인 영역 안쪽 클릭이면 무시
      if (mainRef.current?.contains(target)) return;

      // 바깥 클릭 시 선택 초기화
      setSelectedCustomer(null);
      setChannel(null);
      // setUserId(''); // 필요하다면 ID도 초기화 (선택 사항)
    };

    document.addEventListener('pointerdown', handleOutside);
    return () => document.removeEventListener('pointerdown', handleOutside);
  }, []);


  // ============ 4. 렌더링 ===========
  return (
    <div className="app-container min-h-screen">
      <header className="app-header pixel-border bg-black text-white p-6 mb-8 text-center shadow-[6px_6px_0px_0px_rgba(0,0,0,0.2)]">
        <h1 className="text-3xl font-black tracking-tighter">DAPANDA</h1>
        <p className="text-[13px] mt-2 opacity-70 tracking-widest">Hyper-personalization Message Generation System</p>
      </header>

      <main ref={mainRef} className="main-layout">
        {/* 좌측 패널: 설정 */}
        <section className="flex flex-col gap-6">
          <div className="glass-card">
            <h2 className="font-black mb-4 text-sm border-b-2 border-black pb-1 inline-block">1. SELECT PERSONA</h2>
            <div className="grid grid-cols-5 gap-2 mb-4">
              {/* 로딩 중이거나 데이터가 없을 때 최소 5개 슬롯 유지 */}
              {(allPersonas.length > 0 ? allPersonas : [0,1,2,3,4]).map((item, index) => {
                // item이 숫자인지(로딩중) 실제 객체인지 확인
                const customer = typeof item === 'number' ? null : (item as CustomerPersona);
                const isLoaded = !!customer;
                const isSelected = selectedCustomer?.user_id === customer?.user_id;

                return (
                  <button 
                    key={customer ? customer.user_id : index}
                    onClick={() => isLoaded && handlePersonaClick(customer)}
                    disabled={!isLoaded} 
                    className={`
                      aspect-square font-black text-sm transition-all duration-100 border-2 border-black
                      ${!isLoaded 
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed border-dashed' // 로딩/빈슬롯
                        : isSelected
                          ? 'bg-yellow-300 text-black shadow-none translate-x-[2px] translate-y-[2px]' // 선택됨
                          : 'bg-white text-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-1 hover:bg-yellow-50' // 기본
                      }
                    `}
                  >
                    {isLoaded ? `P${index + 1}` : '...'}
                  </button>
                );
              })}
            </div>

            {/* 2. 컨트롤 바 (+ ADD 와 🗑️ DELETE) */}
            <div className="flex justify-between items-center mb-6 pt-2 border-t-2 border-black border-dashed">
              
              {/* 왼쪽: + ADD 버튼 */}
              <button 
                onClick={handleAddPersona}
                className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-black font-bold text-xs shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-[1px] active:translate-y-[1px] hover:bg-gray-50 transition-all"
              >
                <span className="text-lg leading-none">+</span> ADD
              </button>

              {/* 오른쪽: 쓰레기통 (삭제) 버튼 */}
              <button 
                onClick={handleDeletePersona}
                disabled={!selectedCustomer} // 선택된게 없으면 비활성화
                className={`
                  flex items-center gap-2 px-4 py-2 border-2 border-black font-bold text-xs shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-[1px] active:translate-y-[1px] transition-all
                  ${selectedCustomer 
                    ? 'bg-red-500 text-white hover:bg-red-600 cursor-pointer' // 활성 (빨강)
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed' // 비활성 (회색)
                  }
                `}
                title="선택한 페르소나 삭제 (P1~P5 제외)"
              >
                TRASH 🗑️
              </button>
            </div>
            
            {/* 모달은 이제 안 쓰거나 나중에 연결 (일단 유지) */}
            <AddPersonaModal 
              isOpen={isModalOpen} 
              onClose={() => setIsModalOpen(false)} 
              onApply={() => {}}
            />
        

            <h2 className="font-black mb-4 text-sm border-b-2 border-black pb-1 inline-block">2. MESSAGE CHANNEL</h2>
            <div className="space-y-6">
              {/* 채널 선택 */}
              <div className="text-left">
                <ChannelSelector selected={channel} onSelect={setChannel} disabled={loading} />
              </div>
            </div>

            <h2 className="font-black mb-4 mt-8 text-sm border-b-2 border-black pb-1 inline-block">3. CONTEXT (DEMO)</h2>
             <div className="space-y-4 text-left">
               
               {/* Brand Selector */}
               <div>
                 <label className="block text-xs font-bold mb-1">BRAND</label>
                 <select 
                   value={brand} 
                   onChange={(e) => setBrand(e.target.value)}
                   className="w-full border-2 border-black p-2 text-sm font-bold shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] focus:outline-none focus:bg-yellow-50"
                 >
                   <option value="이니스프리">🌿 이니스프리 (Innisfree)</option>
                   <option value="설화수">🌸 설화수 (Sulwhasoo)</option>
                   <option value="헤라">💄 헤라 (HERA)</option>
                   <option value="에뛰드">🎀 에뛰드 (Etude)</option>
                 </select>
               </div>

               {/* Reason Selector */}
               <div>
                 <label className="block text-xs font-bold mb-1">CRM REASON</label>
                 <select 
                   value={reason} 
                   onChange={(e) => setReason(e.target.value)}
                   className="w-full border-2 border-black p-2 text-sm font-bold shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] focus:outline-none focus:bg-yellow-50"
                 >
                   <option value="신제품 출시 이벤트">🚀 신제품 출시 (New Product)</option>
                   <option value="날씨">🌦️ 날씨 기반 추천 (Weather)</option>
                   <option value="할인행사">💸 할인 행사 (Sale)</option>
                   <option value="일반홍보">📢 일반 홍보 (General)</option>
                 </select>
               </div>

               {/* Weather Detail Input (Conditional) */}
               {reason === '날씨' && (
                 <div className="animate-fade-in-up">
                   <label className="block text-xs font-bold mb-1 text-blue-600">WEATHER DETAIL</label>
                   <input
                     type="text"
                     value={weatherDetail}
                     onChange={(e) => setWeatherDetail(e.target.value)}
                     placeholder="예: 비가 오고 습함, 폭염 주의보"
                     className="w-full border-2 border-blue-500 p-2 text-sm font-bold shadow-[2px_2px_0px_0px_rgba(59,130,246,1)] focus:outline-none bg-blue-50"
                   />
                 </div>
               )}

             </div>
          </div>

          <div className="glass-card bg-[#E0F2FE] border-black border-[3px] shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
            <div className="flex items-center gap-2 mb-3 border-b-2 border-black/10 pb-2">
              <div className="w-8 h-8 bg-white border-2 border-black flex items-center justify-center text-lg shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                {selectedCustomer ? '👤' : '❓'}
              </div>
              <div className="flex flex-col">
                <h3 className="text-[10px] font-black uppercase text-gray-500">Selected Persona</h3>
                {selectedCustomer && (
                  <span className="text-xs font-black">{selectedCustomer.user_id}</span>
                )}
              </div>
            </div>
            
            {selectedCustomer ? (
              <div className="text-left space-y-3">
                {/* 이름 & 등급 */}
                <div className="flex justify-between items-center bg-white/50 p-2 rounded border border-black/5">
                  <span className="text-sm font-black text-ellipsis overflow-hidden whitespace-nowrap">
                    {safeRender(selectedCustomer.name, '고객')}
                  </span>
                  <span className="bg-black text-white px-2 py-0.5 text-[10px] font-bold rounded-full shrink-0">
                    {safeRender(selectedCustomer.membership_level, 'GEN')}
                  </span>
                </div>
                
                {/* 태그 영역 (피부타입 + 키워드) */}
                <div className="space-y-1">
                  <p className="text-[9px] font-bold text-gray-500 uppercase">Tags & Keywords</p>
                  <div className="flex flex-wrap gap-1.5 min-h-[20px]">
                    {/* 안전하게 배열인지 확인 후 렌더링 */}
                    {(() => {
                        const skinTypes = Array.isArray(selectedCustomer.skin_type) ? selectedCustomer.skin_type : [];
                        const keywords = Array.isArray(selectedCustomer.keywords) ? selectedCustomer.keywords : [];
                        const tags = [...skinTypes, ...keywords];
                        
                        // 문자열로 데이터가 들어올 경우에 대한 방어 로직 (CSV 등)
                        if (tags.length === 0 && typeof selectedCustomer.skin_type === 'string') {
                            tags.push(selectedCustomer.skin_type);
                        }

                        if (tags.length === 0) return <span className="text-[9px] text-gray-400">No tags</span>;

                        return tags.slice(0, 5).map((tag, i) => (
                        <span key={i} className="bg-white border-2 border-black px-1.5 py-0.5 text-[9px] font-bold shadow-[1px_1px_0px_0px_rgba(0,0,0,1)]">
                            #{safeRender(tag)}
                        </span>
                        ));
                    })()}
                  </div>
                </div>

                {/* 선호 톤 영역 */}
                <div className="pt-2 border-t-2 border-dashed border-black/20">
                  <p className="text-[9px] font-bold text-gray-500 uppercase mb-1">Preferred Tone</p>
                  <p className="text-[11px] leading-snug text-gray-800 bg-yellow-100 p-2 border border-black rounded-sm relative">
                    <span className="absolute -top-1.5 -left-1 text-[15px]">🎨</span>
                    <span className="font-black break-all">
                     {safeRender(selectedCustomer.preferred_tone, ' - ')}
                    </span>
                  </p>
                  <p className="text-[9px] font-bold text-gray-500 uppercase mb-1 mt-2">Persona Category</p>
                  <p className="text-[11px] leading-snug text-gray-800 bg-yellow-100 p-2 border border-black rounded-sm relative">
                    <span className="absolute -top-1.5 -left-1 text-[15px]">📂</span>
                    <span className="font-black break-all">
                      {safeRender(selectedCustomer.persona_category, ' - ')}
                    </span>
                  </p>
                </div>
              </div>
            ) : (
              <div className="py-4 text-center opacity-50">
                <p className="text-xs font-bold mb-1">NO PERSONA SELECTED</p>
                <p className="text-[10px]">상단의 P 버튼을 눌러 고객을 선택하세요.</p>
              </div>
            )}
          </div>
        </section>

        {/* 우측 패널: 결과 */}
        <section className="flex flex-col gap-6">
          <div className="glass-card flex-1 flex flex-col min-h-[400px]">
            <div className="bg-gray-100 border-b-4 border-black -m-6 mb-6 p-4">
              <h2 className="font-black text-lg">CRM MESSAGE GEN</h2>
            </div>

            <div className="flex-1 flex flex-col items-center justify-center">
              {!message && !loading && !error && (
                <div className="flex flex-col items-center gap-6">
                  <button 
                    onClick={handleGenerateClick}
                    disabled={!canGenerate}
                    className={`
                      bg-green-400 hover:bg-green-500 text-black px-12 py-6 text-2xl font-black
                      border-4 border-black
                      shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]
                      active:shadow-none active:translate-x-1 active:translate-y-1
                      disabled:bg-gray-300 disabled:text-gray-500
                      disabled:shadow-none disabled:cursor-not-allowed
                    `}
                  >
                    GENERATE!
                  </button>
                </div>
              )}

              {loading && <LoadingSpinner />}
              
              {error && (
                <ErrorMessage message={error} onRetry={() => setError(null)} />
              )}

              {/* --- 결과 화면 영역 --- */}
              {message && !loading && (
                <div className="w-full text-left animate-fade-in-up flex flex-col h-full">
                  <div className="flex items-center gap-2 mb-4">
                     <h2 className="font-black text-lg border-b-4 border-black inline-block leading-none">RESULT</h2>
                  </div>
                  
                  {/* 메시지 내용 박스 (기존 스타일 유지: 각진 테두리) */}
                  <div className="bg-white p-6 border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] flex-1 mb-6">
                    <MessageDisplay message={message} />
                  </div>

                  {/* [버튼 영역] 작고 각지게! */}
                  <div className="flex gap-3 mt-auto">
                    
                    {/* 1. 채널만 변경 (주황색, 각진 버튼) */}
                    <button 
                      onClick={handleNextMessage}
                      className="flex-1 bg-[#FFB74D] hover:bg-[#FFA726] text-black py-3 border-2 border-black font-bold text-sm shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-[2px] active:translate-y-[2px] transition-all"
                    >
                      🔙 다른 채널 선택
                    </button>

                    {/* 2. 처음으로 (회색, 각진 버튼) */}
                    <button 
                      onClick={handleReset}
                      className="flex-1 bg-gray-100 hover:bg-gray-200 text-black py-3 border-2 border-black font-bold text-sm shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-[2px] active:translate-y-[2px] transition-all"
                    >
                      🔚 처음으로
                    </button>
                  </div>
                </div>
              )}
              {/* --- 결과 화면 영역 교체 끝 --- */}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;