/**
 * LoadingSpinner Component
 * 로딩 상태 표시 컴포넌트
 */

export function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <div className="relative w-16 h-16">
        <div className="absolute top-0 left-0 w-full h-full border-4 border-pink-200 rounded-full"></div>
        <div className="absolute top-0 left-0 w-full h-full border-4 border-pink-500 rounded-full border-t-transparent animate-spin"></div>
      </div>
      <div className="text-center">
        <p className="text-gray-700 font-medium">메시지 생성 중...</p>
        <p className="text-sm text-gray-500 mt-1">AI가 맞춤형 메시지를 작성하고 있습니다</p>
      </div>
    </div>
  );
}
