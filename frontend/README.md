# Blooming CRM Frontend

Blooming CRM의 사용자 인터페이스를 담당하는 React 애플리케이션입니다.

## 🌟 주요 기능

- **Persona Maker**: 마케터가 타겟 고객의 페르소나(연령, 피부타입, 고민 등)를 설정하는 직관적인 UI 제공.
- **Message Dashboard**: LLM이 생성한 마케팅 메시지를 실시간으로 확인하고 수정할 수 있는 에디터.
- **Target Audience Visualization**:
  - 선택된 페르소나에 해당하는 **Similar User IDs** 목록 표시.
  - 전체 타겟 모수와 예상 도달률 시각화.
- **History Management**: 과거 생성된 캠페인 및 메시지 이력 조회.

## 🛠️ 기술 스택

- **Core**: React 18, TypeScript
- **Build**: Vite
- **Styling**: Tailwind CSS, Shadcn/ui (예상)
- **State Management**: Zustand
- **Data Fetching**: Axios / TanStack Query
- **Routing**: React Router

## 📂 폴더 구조

```
src/
├── assets/         # 이미지 및 정적 파일
├── components/     # 공통 UI 컴포넌트
├── data/           # 정적 데이터 (Persona 옵션 등)
├── features/       # 기능별 모듈
│   ├── persona/    # 페르소나 설정 관련 컴포넌트
│   ├── dashboard/  # 메인 대시보드
│   ├── shared/     # 공유 컴포넌트 (ResultCard 등)
│   └── ...
├── services/       # API 호출 로직 (api.ts)
├── store/          # 전역 상태 관리 (Zustand)
└── types/          # TypeScript 타입 정의
```

## 🚀 실행 방법

1. **의존성 설치**
   ```bash
   npm install
   ```

2. **개발 서버 실행**
   ```bash
   npm run dev
   ```
   http://localhost:5173 에서 접속 가능합니다.

3. **빌드**
   ```bash
   npm run build
   ```
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
