import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { ApiService } from '../../services/api';
import { CustomerService } from '../../services/customerService';
import { LogService } from '../../services/logService';
import { ResultCard } from '../shared/ResultCard'; 

export function StickySummary() {
  const {
    intention,
    selectedPersonaId,
    selectedCustomer,
    simulationData,
    isBrandTargeting,
    targetBrand,
    selectedChannel,
    personas,
    resetAll,

    isGenerating,
    setIsGenerating,
    generatedResult,
    setGeneratedResult,
    loadLogs // 히스토리 새로고침용
  } = useAppStore();

  // 🔽 selectedPersonaId로 실제 persona 객체를 찾아서 (id / personaType / name 등) 활용
  const selectedPersona = selectedPersonaId
    ? personas.find((p) => String(p.id) === String(selectedPersonaId))
    : null;

  const personaName = selectedPersona?.name || 'Select Persona';

  // 진행률 계산
  const steps = [
    { label: 'Intention', done: intention != null },
    { label: 'Persona', done: selectedPersonaId != null },
    { label: 'Channel', done: selectedChannel != null },
  ];

  const completedCount = steps.filter((s) => s.done).length;
  const progress = Math.round((completedCount / steps.length) * 100);
  const isReady = progress === 100;

  const BatteryProgress = ({ progress = 0 }) => {
    const p = Math.max(0, Math.min(100, Number(progress) || 0));
    const segSize = 100 / 3;
    const fillFor = (idx: number) => {
      const start = idx * segSize;
      const ratio = (p - start) / segSize;
      const clamped = Math.max(0, Math.min(1, ratio));
      return `${clamped * 100}%`;
    };
    return (
      <div className="flex items-center gap-2">
        <div className="flex items-center">
          <div className="flex overflow-hidden border-2 border-black bg-white">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className={`relative h-3 w-5 ${i !== 2 ? 'border-r-2 border-black' : ''} bg-white`}
              >
                <div
                  className="absolute inset-y-0 left-0 bg-[#00D06C] transition-all duration-300"
                  style={{ width: fillFor(i) }}
                />
              </div>
            ))}
          </div>
        </div>
        <span className="text-xs font-black tabular-nums">{Math.round(p)}%</span>
      </div>
    );
  };

  const handleGenerate = async () => {
    if (!selectedChannel) return;
    if (isGenerating) return;

    // 선택된 고객의 user_id 사용 (없으면 기본값 "user_0001")
    const targetUserId = selectedCustomer?.user_id || 'user_0001';
    setIsGenerating(true);
    setGeneratedResult(null);

    try {
      // 1) DB Sync (프로필 저장) - 선택된 userId 기준으로 저장
      await CustomerService.updateCustomerProfile(String(targetUserId), simulationData);

      // 2) API Call - ID + 상황 정보만 전달 (beautyProfile 제거)
      const params = {
        userId: String(targetUserId), 

        // 상황 정보 (Context)
        channel: selectedChannel || 'SMS',
        intention: intention || '프로모션',
        hasBrand: true, // 기존 요구사항 기준 (필요하면 isBrandTargeting로 교체 가능)
        targetBrand: targetBrand || '마몽드',

        // 기존 state에 날씨/시즌이 없어서 기본값으로 처리
        season: '봄',
        weatherDetail: '맑음',

        // 페르소나 선택 (AI 로직 분기용)
        persona: selectedPersonaId || 'P1',
      };

      // 서비스 구현에 맞춰 result.message 형태 우선 지원 + 기존 response.data 형태도 안전 처리
      const result: any = await ApiService.generateMessage(params);

      const message =
        result?.message ??
        result?.data?.message ??
        result?.data?.content ??
        result?.content ??
        null;

      if (message) {
        setGeneratedResult(message);

        // 3) History Save (로그 저장)
        await LogService.saveLog({
          user_id: String(targetUserId),
          channel: selectedChannel,
          intention: intention || 'PROMOTION',
          content: message,
          beauty_profile: simulationData, // 기존 로그 스키마 유지(선택)
        });

        await loadLogs(String(targetUserId));
      } else {
        console.error('메시지 응답 없음', result);
        alert('메시지 응답이 없습니다.');
      }
    } catch (error) {
      console.error('Generate Error:', error);
      alert('오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReset = () => {
    if (window.confirm('모든 설정을 초기화하시겠습니까?')) {
      resetAll();
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="p-4 border-2 border-black bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
        {/* 헤더 */}
        <div className="flex justify-between items-center mb-4 border-b-2 border-black border-dashed pb-2">
          <h3 className="font-black text-sm italic">STATUS CHECK</h3>
          <BatteryProgress progress={progress} />
        </div>

        {/* 진행 상태 */}
        <ul className="space-y-3 mb-6">
          {steps.map((step, idx) => (
            <li key={idx} className="flex items-center justify-between text-sm">
              <span
                className={`font-bold transition-opacity ${
                  step.done ? 'opacity-100 text-black' : 'opacity-30 text-gray-500'
                }`}
              >
                {idx + 1}. {step.label}
              </span>
              <span>{step.done ? '✅' : '⬜'}</span>
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
            <span className="font-bold">{personaName}</span>
          </div>
          <div className="flex gap-2 items-center">
            <span>📡</span>
            <span className={`font-bold ${selectedChannel ? 'text-black' : 'text-gray-400'}`}>
              {selectedChannel || 'Not Selected'}
            </span>
          </div>
        </div>

        {/* 버튼들 */}
        <div className="space-y-6">
          <button
            onClick={handleReset}
            className="w-full py-2 text-xs font-black text-red-600 bg-red-50 hover:bg-red-100 border-2 border-black transition-all shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-[1px] active:translate-y-[1px]"
          >
            🗑️ RESET ALL
          </button>
          <div className="h-px bg-black/30" />
          <button
            onClick={handleGenerate}
            disabled={!isReady || isGenerating}
            className={`
              w-full py-4 text-sm font-black uppercase tracking-wider border-2 border-black transition-all
              flex justify-center items-center gap-2
              ${
                isReady
                  ? 'bg-[#00D06C] hover:bg-[#00b55e] text-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-[2px] active:translate-y-[2px] cursor-pointer'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed border-gray-300'
              }
            `}
          >
            {isGenerating ? (
              <>
                <span className="animate-spin">⏳</span> GENERATING...
              </>
            ) : (
              <>🚀 GENERATE</>
            )}
          </button>
        </div>
      </div>

      {/* 결과 미리보기 카드 (히스토리 리스트는 제거됨) */}
      {generatedResult && selectedChannel && <ResultCard content={generatedResult} channel={selectedChannel} />}
    </div>
  );
}
