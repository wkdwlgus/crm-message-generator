import React, { useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';

export const HistoryFeed = () => {
  const { 
    messageLogs, 
    selectedPersonaId, 
    loadLogs, 
    personas 
  } = useAppStore();

  const currentPersona = personas.find(p => p.id === selectedPersonaId);

  // 탭이 활성화되거나 페르소나가 바뀌면 로그 로딩
  useEffect(() => {
    if (selectedPersonaId) {
      loadLogs(selectedPersonaId);
    }
  }, [selectedPersonaId, loadLogs]);

  if (!selectedPersonaId) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 font-bold italic">
        SELECT A PERSONA TO VIEW HISTORY
      </div>
    );
  }

  if (messageLogs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <span className="text-4xl mb-2">📭</span>
        <h3 className="font-black text-lg">NO HISTORY YET</h3>
        <p className="text-xs text-gray-500 mt-1">
          우측의 GENERATE 버튼을 눌러 메시지를 생성해보세요.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-2">
      <div className="flex items-center justify-between pb-4 border-b-2 border-black border-dashed">
        <h2 className="text-lg font-black italic">
          MESSAGE TIMELINE <span className="text-gray-400 font-normal not-italic text-sm ml-2">with {currentPersona?.name}</span>
        </h2>
        <span className="bg-black text-white text-xs font-bold px-2 py-1 rounded-full">
          Total {messageLogs.length}
        </span>
      </div>

      <div className="flex flex-col gap-6 max-h-[600px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-black scrollbar-track-gray-100">
        {messageLogs.map((log) => (
          <div key={log.id} className="group relative flex gap-4">
            {/* 타임라인 선 */}
            <div className="absolute left-[19px] top-10 bottom-[-24px] w-0.5 bg-gray-200 group-last:hidden"></div>

            {/* 아이콘 */}
            <div className="relative z-10 w-10 h-10 rounded-full border-2 border-black bg-white flex items-center justify-center flex-shrink-0 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
               <span className="text-lg">
                 {log.channel === 'SMS' ? '💬' : log.channel === 'KAKAO' ? '💛' : '📱'}
               </span>
            </div>

            {/* 내용 카드 */}
            <div className="flex-1 border-2 border-black bg-white p-5 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-sm transition-all">
              <div className="flex justify-between items-start mb-3">
                <div className="flex gap-2 items-center">
                  <span className="font-black bg-black text-white px-2 py-0.5 text-xs uppercase">
                    {log.channel}
                  </span>
                  <span className="text-[10px] font-bold text-blue-600 border border-blue-600 px-1.5 rounded-sm uppercase">
                    {log.intention || 'PROMOTION'}
                  </span>
                </div>
                <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wide">
                  {new Date(log.created_at).toLocaleString()}
                </span>
              </div>
              
              <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                {log.content}
              </p>

              {/* 당시 사용된 뷰티 프로필 스냅샷 */}
              <div className="mt-4 pt-3 border-t border-gray-100 flex flex-wrap gap-2 text-[10px] text-gray-400 font-medium">
                <span>Snapshot:</span>
                <span>{log.beauty_profile?.skin_type?.join(', ')}</span>
                <span>/</span>
                <span>{log.beauty_profile?.preferred_tone}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};