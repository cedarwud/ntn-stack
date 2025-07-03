# NTN Stack 代碼規範

## TypeScript 規範
- 使用 TypeScript 嚴格模式
- 明確定義介面和類型
- 使用 PascalCase 命名組件和類型
- 使用 camelCase 命名變數和函數
- 使用 kebab-case 命名文件

## React 規範
- 使用函數組件和 Hooks
- 使用 React.memo 優化性能
- 使用 useMemo 和 useCallback 穩定引用
- 組件名稱使用 PascalCase
- Props 介面以 Props 結尾

## 文件命名
- 組件文件：`ComponentName.tsx`
- 樣式文件：`ComponentName.scss`
- 類型定義：`types/index.ts`
- 工具函數：`utils/functionName.ts`

## 目錄結構
```
src/
├── components/
│   ├── domains/           # 業務領域組件
│   ├── shared/           # 共享組件
│   └── layout/           # 佈局組件
├── pages/                # 頁面組件
├── hooks/                # 自定義 Hooks
├── types/                # 類型定義
├── utils/                # 工具函數
└── styles/               # 全局樣式
```

## Chart.js 使用
- 優先使用原生 Chart.js 而非 react-chartjs-2
- 使用 React.memo 避免不必要重新渲染
- 使用 useRef 管理圖表實例
- 使用 update('none') 避免動畫閃爍

## 性能優化
- 使用 React.memo 包裝組件
- 使用 useMemo 穩定計算結果
- 使用 useCallback 穩定回調函數
- 避免在每次渲染時創建新物件