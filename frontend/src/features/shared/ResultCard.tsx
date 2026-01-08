import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';

interface ResultCardProps {
  content: string;
  channel: string;
  similarUserIds?: string[];  // [NEW] 유사 유저 ID 리스트
}

export function ResultCard({ content, channel, similarUserIds = [] }: ResultCardProps) {
  const [copied, setCopied] = useState(false);
  
  console.log('🔍 [ResultCard DEBUG] Received props:', { 
    content: content?.substring(0, 50), 
    channel, 
    similarUserIds: similarUserIds?.length,
    similarUserIdsSample: similarUserIds?.slice(0, 5)
  });

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
      <div className="p-4 bg-yellow-50 min-h-[120px] text-sm text-gray-900 leading-relaxed">
        <ReactMarkdown 
          remarkPlugins={[remarkBreaks]}
          components={{
            ul: ({node, ...props}) => <ul className="list-disc pl-5 my-2" {...props} />,
            ol: ({node, ...props}) => <ol className="list-decimal pl-5 my-2" {...props} />,
            strong: ({node, ...props}) => <strong className="font-black" {...props} />,
            a: ({node, ...props}) => <a className="text-blue-600 underline font-bold" {...props} />,
            p: ({node, ...props}) => <p className="mb-1" {...props} />,
          }}
        >
          {content}
        </ReactMarkdown>
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

      {/* 유사 유저 ID 표시 */}
      {similarUserIds && similarUserIds.length > 0 && (
        <div className="border-t-2 border-black p-4 bg-blue-50">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm">👥</span>
            <span className="font-bold text-xs uppercase tracking-wider">
              Similar Users ({similarUserIds.length})
            </span>
          </div>
          <div className="text-xs text-gray-700 max-h-32 overflow-y-auto">
            <div className="flex flex-wrap gap-2">
              {similarUserIds.slice(0, 50).map((userId, idx) => (
                <span 
                  key={idx}
                  className="px-2 py-1 bg-white border border-gray-300 rounded font-mono text-[10px]"
                >
                  {userId}
                </span>
              ))}
              {similarUserIds.length > 50 && (
                <span className="px-2 py-1 text-gray-500 italic text-[10px]">
                  ... +{similarUserIds.length - 50} more
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}