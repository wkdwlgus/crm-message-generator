import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query' // 추가됨
import './index.css'
import App from './App.tsx'

// 데이터 비서(Client) 생성
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1, // API 실패 시 1번만 재시도 (너무 많이 하면 사용자 답답함)
      refetchOnWindowFocus: false, // 탭 전환했다 돌아와도 재요청 안 함 (선택사항)
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* 앱 전체를 감싸서 어디서든 비서를 부를 수 있게 함 */}
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)