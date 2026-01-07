import React, { useState } from 'react';

interface ResultCardProps {
  content: string;
  channel: string;
}

export function ResultCard({ content, channel }: ResultCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-4 border-2 border-black bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] animate-fade-in-up">
      {/* 카드 헤더 */}
      <div className="bg-black text-white px-3 py-2 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="text-lg">🎉</span>
          <span className="font-bold text-xs uppercase tracking-wider">Generated Result</span>
        </div>
        <span className="text-[10px] font-mono bg-gray-800 px-2 py-0.5 rounded">
          {channel}
        </span>
      </div>

      {/* 본문 영역 */}
      <div className="p-4 bg-yellow-50 min-h-[120px]">
        <p className="text-sm font-medium whitespace-pre-wrap leading-relaxed text-gray-900">
          {content}
        </p>
      </div>

      {/* 푸터 / 액션 */}
      <div className="border-t-2 border-black p-2 bg-gray-50 flex justify-end">
        <button
          onClick={handleCopy}
          className={`
            text-xs font-bold px-4 py-2 border-2 border-black transition-all flex items-center gap-2
            ${copied 
              ? 'bg-green-500 text-white shadow-none translate-x-[1px] translate-y-[1px]' 
              : 'bg-white hover:bg-gray-100 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-[2px] active:translate-y-[2px]'
            }
          `}
        >
          {copied ? '✅ COPIED!' : '📋 COPY TEXT'}
        </button>
      </div>
    </div>
  );
}