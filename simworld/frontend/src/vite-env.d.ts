/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GATEWAY_URL: string
  readonly VITE_PORT: string
  // 更多環境變量可以在這裡聲明
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// CSS 模組類型定義
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}

declare module '*.module.scss' {
  const classes: { [key: string]: string };
  export default classes;
}

declare module '*.module.sass' {
  const classes: { [key: string]: string };
  export default classes;
}

// 一般 CSS/SCSS 文件
declare module '*.css';
declare module '*.scss';
declare module '*.sass';

// 圖片和其他資源文件
declare module '*.svg' {
  import * as React from 'react';
  const content: React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
  export default content;
}

declare module '*.png';
declare module '*.jpg';
declare module '*.jpeg';
declare module '*.gif';
declare module '*.webp';
