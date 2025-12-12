/**
 * MessageDisplay Component
 * 생성된 메시지 표시 컴포넌트
 */
import type { GeneratedMessage } from '../types/api';

interface MessageDisplayProps {
  message: GeneratedMessage;
}

export function MessageDisplay({ message }: MessageDisplayProps) {
  const channelIcons: Record<string, string> = {
    SMS: '📱',
    KAKAO: '💬',
    EMAIL: '📧',
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return new Date().toLocaleString('ko-KR');
    return new Date(dateString).toLocaleString('ko-KR');
  };

  return (
    <div className="w-full max-w-2xl bg-white rounded-xl shadow-lg p-6 space-y-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between pb-4 border-b">
        <div className="flex items-center gap-2">
          <span className="text-3xl">{channelIcons[message.channel]}</span>
          <div>
            <h3 className="text-lg font-semibold text-gray-800">
              생성된 메시지
            </h3>
            <p className="text-sm text-gray-500">
              {message.channel} · {formatDate(message.generated_at)}
            </p>
          </div>
        </div>
        <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
          ✓ 법규 준수
        </span>
      </div>

      {/* 메시지 내용 */}
      <div className="bg-gray-50 rounded-lg p-4">
        <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
          {message.message_content}
        </p>
      </div>

      {/* 메타데이터 */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t">
        <div>
          <p className="text-xs text-gray-500 mb-1">고객 ID</p>
          <p className="text-sm font-medium text-gray-700">{message.user_id}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">페르소나</p>
          <p className="text-sm font-medium text-gray-700">{message.persona_id}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">추천 상품</p>
          <p className="text-sm font-medium text-gray-700">{message.product_id}</p>
        </div>
      </div>
    </div>
  );
}
