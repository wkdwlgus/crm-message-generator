/**
 * Blooming CRM Message Generation System
 * 페르소나 기반 초개인화 CRM 메시지 생성 시스템
 */
import { useState } from 'react';
import { UserIdInput } from './components/UserIdInput';
import { ChannelSelector } from './components/ChannelSelector';
import { MessageDisplay } from './components/MessageDisplay';
import { LoadingSpinner } from './components/LoadingSpinner';
import { ErrorMessage } from './components/ErrorMessage';
import { ApiService } from './services/api';
import type { ChannelType, GeneratedMessage } from './types/api';
import './App.css';

function App() {
  const [channel, setChannel] = useState<ChannelType>('SMS');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<GeneratedMessage | null>(null);

  const handleGenerateMessage = async (userId: string) => {
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const response = await ApiService.generateMessage(userId, channel);
      setMessage(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setError(null);
    setMessage(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50">
      <div className="container mx-auto px-4 py-12">
        {/* 헤더 */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-3">
            🌸 Blooming CRM
          </h1>
          <p className="text-lg text-gray-600">
            페르소나 기반 초개인화 메시지 생성 시스템
          </p>
        </div>

        {/* 메인 컨텐츠 */}
        <div className="flex flex-col items-center space-y-8">
          {/* 채널 선택 */}
          <ChannelSelector
            selected={channel}
            onSelect={setChannel}
            disabled={loading}
          />

          {/* 고객 ID 입력 */}
          <UserIdInput
            onSubmit={handleGenerateMessage}
            disabled={loading}
          />

          {/* 로딩 상태 */}
          {loading && <LoadingSpinner />}

          {/* 에러 메시지 */}
          {error && (
            <ErrorMessage
              message={error}
              onRetry={handleRetry}
            />
          )}

          {/* 생성된 메시지 */}
          {message && !loading && !error && (
            <MessageDisplay message={message} />
          )}
        </div>

        {/* 푸터 */}
        <div className="text-center mt-16 text-sm text-gray-500">
          <p>
            Powered by OpenAI GPT-5 · LangGraph · FastAPI · React
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;

