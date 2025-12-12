/**
 * UserIdInput Component
 * 고객 ID 입력 컴포넌트
 */
import { useState } from 'react';

interface UserIdInputProps {
  onSubmit: (userId: string) => void;
  disabled?: boolean;
}

export function UserIdInput({ onSubmit, disabled = false }: UserIdInputProps) {
  const [userId, setUserId] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (userId.trim()) {
      onSubmit(userId.trim());
    }
  };

  // Mock 사용자 ID 선택
  const handleMockUser = (mockId: string) => {
    setUserId(mockId);
    onSubmit(mockId);
  };

  return (
    <div className="w-full max-w-md space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="고객 ID 입력 (예: user_12345)"
          disabled={disabled}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500 disabled:bg-gray-100"
        />
        <button
          type="submit"
          disabled={disabled || !userId.trim()}
          className="px-6 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          생성
        </button>
      </form>

      <div className="space-y-2">
        <p className="text-sm text-gray-600">테스트용 Mock 사용자:</p>
        <div className="flex gap-2">
          <button
            onClick={() => handleMockUser('user_12345')}
            disabled={disabled}
            className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50 transition-colors"
          >
            김아모레 (VVIP)
          </button>
          <button
            onClick={() => handleMockUser('user_67890')}
            disabled={disabled}
            className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50 transition-colors"
          >
            박뷰티 (Gold)
          </button>
        </div>
      </div>
    </div>
  );
}
