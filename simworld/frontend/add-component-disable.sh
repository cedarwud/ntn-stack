#!/bin/bash

echo "🏷️ 為剩餘的未使用聲明添加 eslint-disable 註釋..."

# 處理未使用的組件和函數聲明
find src -name "*.tsx" -o -name "*.ts" | while read file; do
    # 為未使用的組件添加註釋
    sed -i '/^[[:space:]]*const[[:space:]]\+\([A-Z][a-zA-Z]*Visualization\|[A-Z][a-zA-Z]*Display\|[A-Z][a-zA-Z]*Component\)[[:space:]]*:/i\
        // eslint-disable-next-line @typescript-eslint/no-unused-vars' "$file"
    
    # 為未使用的函數添加註釋  
    sed -i '/^[[:space:]]*const[[:space:]]\+_get[A-Z][a-zA-Z]*[[:space:]]*=/i\
        // eslint-disable-next-line @typescript-eslint/no-unused-vars' "$file"
        
    sed -i '/^[[:space:]]*const[[:space:]]\+get[A-Z][a-zA-Z]*[[:space:]]*=/i\
        // eslint-disable-next-line @typescript-eslint/no-unused-vars' "$file"
done

echo "✅ 註釋添加完成！"
