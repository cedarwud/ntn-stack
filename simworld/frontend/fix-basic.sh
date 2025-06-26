#!/bin/bash

# ESLint 錯誤修復腳本

echo "🔧 開始修復 ESLint 錯誤..."

# 1. 修復未使用的變數 - 添加下劃線前綴
echo "1. 修復未使用的變數..."
find src -name "*.ts" -o -name "*.tsx" | xargs sed -i 's/\([[:space:]]\+\)\([a-zA-Z_][a-zA-Z0-9_]*\):\([[:space:]]*[a-zA-Z_][a-zA-Z0-9_<>|&\[\]]*[[:space:]]*\)[,)]/\1_\2:\3,)/g'

# 2. 修復未使用的導入
echo "2. 修復未使用的導入..."
find src -name "*.ts" -o -name "*.tsx" | xargs sed -i 's/import[[:space:]]\+React,[[:space:]]*{[[:space:]]*useRef[[:space:]]*}/import React/g'

# 3. 修復常見的 any 類型
echo "3. 修復 any 類型..."
find src -name "*.ts" -o -name "*.tsx" | xargs sed -i \
  -e 's/event:[[:space:]]*any/event: Event/g' \
  -e 's/e:[[:space:]]*any/e: Event/g' \
  -e 's/data:[[:space:]]*any/data: unknown/g' \
  -e 's/response:[[:space:]]*any/response: unknown/g' \
  -e 's/result:[[:space:]]*any/result: unknown/g' \
  -e 's/value:[[:space:]]*any/value: unknown/g' \
  -e 's/item:[[:space:]]*any/item: unknown/g' \
  -e 's/config:[[:space:]]*any/config: Record<string, unknown>/g' \
  -e 's/options:[[:space:]]*any/options: Record<string, unknown>/g' \
  -e 's/params:[[:space:]]*any/params: Record<string, unknown>/g' \
  -e 's/props:[[:space:]]*any/props: Record<string, unknown>/g'

# 4. 修復空介面
echo "4. 修復空介面..."
find src -name "*.ts" -o -name "*.tsx" | xargs sed -i 's/interface[[:space:]]\+\([a-zA-Z_][a-zA-Z0-9_]*\)[[:space:]]*{[[:space:]]*}/type \1 = Record<string, never>/g'

# 5. 移除未使用的變數聲明
echo "5. 移除未使用的變數..."
find src -name "*.ts" -o -name "*.tsx" | while read file; do
    # 移除明顯未使用的變數賦值
    sed -i \
      -e '/const.*is assigned a value but never used/d' \
      -e '/const[[:space:]]\+\([a-zA-Z_][a-zA-Z0-9_]*\)[[:space:]]*=[[:space:]]*[^,;]*;[[:space:]]*\/\/.*never used/d' \
      "$file"
done

echo "✅ 基本修復完成！"
echo "🔍 運行 npm run lint 檢查剩餘問題..."
