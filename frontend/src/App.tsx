import { useState, useEffect, useRef } from 'react';
import { UserIdInput } from './components/UserIdInput';
import { ChannelSelector } from './components/ChannelSelector';
import { MessageDisplay } from './components/MessageDisplay';
import { LoadingSpinner } from './components/LoadingSpinner';
import { ErrorMessage } from './components/ErrorMessage';
import { AddPersonaModal } from './components/AddPersonaModal';
import { ApiService } from './services/api';
import type { ChannelType, GeneratedMessage } from './types/api';
import './App.css';

function App() {
  const [channel, setChannel] = useState<ChannelType | null>(null);
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<GeneratedMessage | null>(null);
  const [selectedPersonaId, setSelectedPersonaId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [personas, setPersonas] = useState([1, 2, 3, 4, 5]); 
  const canGenerate = selectedPersonaId !== null && channel !== null && !loading;
  const personaRef = useRef<HTMLDivElement | null>(null);
  const channelRef = useRef<HTMLDivElement | null>(null);
  const mainRef = useRef<HTMLDivElement | null>(null);
  
  // 실행 버튼 클릭 시 호출되는 함수
  const handleGenerateClick = async () => {
    if (!userId) {
      alert("고객 ID를 입력해주세요!");
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      // ApiService 호출
      const response = await ApiService.generateMessage(userId, channel);
      setMessage(response.data);
    } catch (err: any) {
      // 에러 메시지 처리 (TypeScript 호환성 수정)
      setError(err?.message || '메시지 생성 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
  const handleOutside = (event: PointerEvent) => {
    const target = event.target as Node;

    // main(앱의 작업영역) 안이면 해제하지 않음
    if (mainRef.current?.contains(target)) return;

    // main 밖이면 둘 다 해제
    setSelectedPersonaId(null);
    setChannel(null);
  };

  document.addEventListener('pointerdown', handleOutside);
  return () => document.removeEventListener('pointerdown', handleOutside);
}, []);

  return (
    <div className="app-container min-h-screen">
      {/* 찰리 스타일 헤더 */}
      <header className="app-header pixel-border bg-black text-white p-6 mb-8 text-center shadow-[6px_6px_0px_0px_rgba(0,0,0,0.2)]">
        <h1 className="text-3xl font-black tracking-tighter">DAPANDA</h1>
        <p className="text-[13px] mt-2 opacity-70 tracking-widest">Hyper-personalization Message Generation System</p>
      </header>

      <main ref={mainRef} className="main-layout">
        {/* 좌측 패널: 설정 */}
        <section className="flex flex-col gap-6">
          <div className="glass-card">
            <h2 className="font-black mb-4 text-sm border-b-2 border-black pb-1 inline-block">1. SELECT PERSONA</h2>
            <div 
               className="grid grid-cols-5 gap-2 mb-6">
              {[1, 2, 3, 4, 5].map((id) => (
                <button 
                  key={id}
                  onClick={() => setSelectedPersonaId(prev => (prev === id ? null : id))}
                  className={`py-3 font-bold border-2 border-black transition-all ${
                    selectedPersonaId === id ? 'bg-yellow-300 shadow-none translate-x-1 translate-y-1' : 'bg-white shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]'
                  }`}
                >
                  P{id}
                </button>
              ))}
              <AddPersonaModal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)} 
                onApply={(schema) => {
                  console.log("선택된 스키마:", schema);
                  // 1단계 완료 조건: 새 페르소나 번호를 리스트에 추가
                  setPersonas([...personas, personas.length + 1]);
                  setIsModalOpen(false);
                  alert(`${schema}가 적용된 페르소나가 추가되었습니다!`);
                }}
              />

              
              <button 
                onClick={() => setIsModalOpen(true)}
                className="py-3 font-bold border-2 border-dashed border-black 
             bg-gray-100 hover:bg-yellow-100
             transition-all shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
              >
                + ADD
              </button>
            </div>
            <h2 className="font-black mb-4 text-sm border-b-2 border-black pb-1 inline-block">2. Message Channel</h2>
            <div className="space-y-6">
              {/* 채널 선택 */}
              <div className="text-left">
                <ChannelSelector selected={channel} onSelect={setChannel} disabled={loading} />
              </div>
            </div>
          </div>

          {/* 페르소나 정보 노출 영역 */}
          <div className="glass-card bg-blue-50 border-dashed border-2">
            <h3 className="text-[10px] font-black mb-2">PERSONA_INFO_LOG</h3>
            <p className="text-xs font-mono">ID: {selectedPersonaId} | STATUS: READY</p>
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

              {message && !loading && (
                <div className="w-full text-left">
                  <h2 className="font-black mb-4 text-sm uppercase underline decoration-4">Result Message</h2>
                  <MessageDisplay message={message} />
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;