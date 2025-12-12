/**
 * ErrorMessage Component
 * 에러 메시지 표시 컴포넌트
 */

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="w-full max-w-md bg-red-50 border-2 border-red-200 rounded-xl p-6 space-y-4">
      <div className="flex items-start gap-3">
        <span className="text-3xl">❌</span>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-red-800 mb-2">
            오류가 발생했습니다
          </h3>
          <p className="text-sm text-red-600">{message}</p>
        </div>
      </div>
      
      {onRetry && (
        <button
          onClick={onRetry}
          className="w-full px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors font-medium"
        >
          다시 시도
        </button>
      )}
    </div>
  );
}
