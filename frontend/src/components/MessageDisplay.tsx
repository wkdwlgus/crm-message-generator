/**
 * MessageDisplay Component
 * Phase 7: 복사 기능 + 찰리 픽셀 스타일 적용
 */
import { useState } from 'react';
import type { GeneratedMessage } from '../types/api';

interface MessageDisplayProps {
  message: GeneratedMessage;
}

export function MessageDisplay({ message }: MessageDisplayProps) {
  const [copied, setCopied] = useState(false);

  // 채널별 아이콘 설정 (Phase 6에서 확장한 채널 대응)
  const channelIcons: Record<string, string> = {
    APP_PUSH: '📱',
    SMS: '💬',
    KAKAO: '💛',
    EMAIL: '📧',
  };

  const handleCopy = async () => {
    try {
      // 기존 코드의 필드명인 message_content를 사용합니다.
      await navigator.clipboard.writeText(message.content || (message as any).message_content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('복사 실패:', err);
    }
  };

  return (
    <div className="w-full space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* 픽셀 스타일 메시지 카드 */}
      <div className="relative p-6 border-[3px] border-black bg-white shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]">
        
        {/* 상단 태그: 채널 표시 */}
        <div className="absolute -top-4 left-4 bg-black text-white px-3 py-1 text-[10px] font-black uppercase tracking-tighter border-2 border-black">
          {channelIcons[message.channel] || '✨'} {message.channel}
        </div>

        {/* 메시지 본문 영역 */}
        <div className="mt-2 min-h-[120px] bg-gray-50 border-2 border-dashed border-gray-300 p-4">
          <p className="text-sm font-mono leading-relaxed text-black whitespace-pre-wrap">
            {message.content || (message as any).message_content}
          </p>
        </div>

        {/* 하단 메타 정보 (고객 ID, 페르소나 등) */}
        <div className="mt-4 flex flex-wrap gap-4 text-[10px] font-bold text-gray-500 border-t-2 border-black pt-4">
          <div className="flex flex-col">
            <span className="text-black uppercase">Target User</span>
            <span>{message.user_id || 'UNKNOWN'}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-black uppercase">Persona ID</span>
            <span>{message.persona_id || 'N/A'}</span>
          </div>
        </div>

        {/* 복사 버튼: 찰리 스타일 노란색 버튼 */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleCopy}
            className={`
              px-6 py-2 border-[3px] border-black font-black text-xs transition-all
              ${copied 
                ? 'bg-green-400 translate-x-1 translate-y-1 shadow-none' 
                : 'bg-yellow-300 hover:bg-yellow-400 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-1 active:translate-y-1'
              }
            `}
          >
            {copied ? '✓ COPIED!' : 'COPY MESSAGE'}
          </button>
        </div>
      </div>
    </div>
  );
}