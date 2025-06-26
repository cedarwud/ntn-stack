#!/bin/bash

echo "🔄 撤銷有問題的修復..."

# 恢復組件名稱 (移除下劃線前綴)
find src -name "*.tsx" -o -name "*.ts" | while read file; do
    # 恢復 React 組件名稱
    sed -i 's/const _\([A-Z][a-zA-Z]*Visualization\)/const \1/g' "$file"
    sed -i 's/const _\([A-Z][a-zA-Z]*Component\)/const \1/g' "$file"
    sed -i 's/const _\([A-Z][a-zA-Z]*Widget\)/const \1/g' "$file"
    sed -i 's/const _\([A-Z][a-zA-Z]*Panel\)/const \1/g' "$file"
done

echo "✅ 撤銷完成！"
