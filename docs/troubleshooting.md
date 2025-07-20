# NTN-Stack 故障排除手冊

## 概述

本手冊提供 NTN-Stack 系統常見問題的診斷和解決方案。按照問題類型分類，提供系統性的故障排除步驟。

## 快速診斷檢查清單

在深入故障排除之前，請先執行以下快速檢查：

- [ ] 網路連接正常
- [ ] 瀏覽器版本支援（Chrome 90+, Firefox 88+, Safari 14+）
- [ ] JavaScript 已啟用
- [ ] 瀏覽器控制台無錯誤訊息
- [ ] 系統服務狀態正常

## 系統連接問題

### 問題：無法訪問系統

**症狀**:
- 頁面無法載入
- 顯示「連接超時」錯誤
- 白屏或載入中狀態

**診斷步驟**:

1. **檢查網路連接**
   ```bash
   # 測試網路連通性
   ping ntn-stack.example.com
   
   # 檢查 DNS 解析
   nslookup ntn-stack.example.com
   ```

2. **檢查服務狀態**
   ```bash
   # 檢查後端服務
   curl -I http://localhost:8000/health
   
   # 檢查前端服務
   curl -I http://localhost:3000
   ```

3. **檢查防火牆設定**
   - 確認端口 8000 (後端) 和 3000 (前端) 已開放
   - 檢查企業防火牆規則

**解決方案**:
- 重啟網路連接
- 聯繫網路管理員檢查防火牆
- 嘗試使用不同網路環境
- 清除 DNS 緩存

### 問題：API 請求失敗

**症狀**:
- 圖表不顯示數據
- 操作無響應
- 控制台顯示 HTTP 錯誤

**診斷步驟**:

1. **檢查 API 狀態**
   ```bash
   # 檢查 API 健康狀態
   curl http://localhost:8000/health
   
   # 測試具體 API 端點
   curl http://localhost:8000/api/sib19/current
   ```

2. **查看瀏覽器控制台**
   - 按 F12 開啟開發者工具
   - 查看 Console 標籤的錯誤訊息
   - 檢查 Network 標籤的請求狀態

**解決方案**:
- 重新整理頁面
- 清除瀏覽器緩存
- 檢查後端服務是否運行
- 驗證 API 端點配置

## 測量事件問題

### 問題：測量事件不啟動

**症狀**:
- 點擊「開始測量」無反應
- 狀態始終顯示「待機」
- 無測量數據產生

**診斷步驟**:

1. **檢查參數配置**
   - 驗證所有必要參數已設定
   - 確認參數值在有效範圍內
   - 檢查座標格式是否正確

2. **檢查系統資源**
   ```bash
   # 檢查 CPU 和記憶體使用
   top
   
   # 檢查磁盤空間
   df -h
   ```

3. **查看後端日誌**
   ```bash
   # 查看應用日誌
   tail -f /var/log/ntn-stack/app.log
   
   # 查看錯誤日誌
   tail -f /var/log/ntn-stack/error.log
   ```

**解決方案**:
- 重新配置參數
- 重啟測量服務
- 檢查系統資源是否充足
- 聯繫技術支援

### 問題：事件不觸發

**症狀**:
- 測量正在運行但事件從不觸發
- 數據顯示正常但無觸發記錄
- 門檻值似乎無效

**診斷步驟**:

1. **檢查門檻值設定**
   - 確認門檻值設定合理
   - 檢查當前測量值是否接近門檻
   - 驗證遲滯值設定

2. **分析測量數據**
   - 觀察數據變化趨勢
   - 檢查數據範圍和門檻值關係
   - 確認測量精度

**解決方案**:
- 調整門檻值到合理範圍
- 減少遲滯值
- 檢查測量條件是否滿足
- 重新校準測量參數

### 問題：數據不準確

**症狀**:
- 測量值明顯異常
- 軌道計算結果不合理
- 時間同步精度差

**診斷步驟**:

1. **檢查輸入數據**
   - 驗證 TLE 數據有效性
   - 檢查時間設定是否正確
   - 確認座標系統一致性

2. **檢查計算引擎**
   ```python
   # 測試軌道計算
   from netstack_api.services.orbit_calculation_engine import OrbitCalculationEngine
   
   engine = OrbitCalculationEngine()
   result = engine.calculate_position(tle_line1, tle_line2, datetime.now())
   print(f"計算結果: {result}")
   ```

**解決方案**:
- 更新 TLE 數據
- 校準時間基準
- 重新初始化計算引擎
- 檢查算法參數

## 性能問題

### 問題：系統響應緩慢

**症狀**:
- 頁面載入時間長
- 圖表更新延遲
- 操作響應慢

**診斷步驟**:

1. **檢查系統資源**
   ```bash
   # 檢查 CPU 使用率
   htop
   
   # 檢查記憶體使用
   free -h
   
   # 檢查磁盤 I/O
   iotop
   ```

2. **分析網路性能**
   ```bash
   # 測試網路延遲
   ping -c 10 api-server
   
   # 測試頻寬
   wget --progress=dot:mega http://api-server/large-file
   ```

3. **檢查緩存效率**
   ```bash
   # 檢查 Redis 狀態
   redis-cli info stats
   
   # 檢查緩存命中率
   curl http://localhost:8000/api/analysis/performance
   ```

**解決方案**:
- 重啟相關服務
- 清理系統緩存
- 優化數據庫查詢
- 增加系統資源

### 問題：記憶體洩漏

**症狀**:
- 記憶體使用持續增長
- 系統變得不穩定
- 最終導致服務崩潰

**診斷步驟**:

1. **監控記憶體使用**
   ```bash
   # 持續監控記憶體
   watch -n 5 'free -h && ps aux --sort=-%mem | head -10'
   ```

2. **分析進程記憶體**
   ```bash
   # 檢查特定進程記憶體
   pmap -d <process_id>
   
   # 使用 valgrind 檢查洩漏
   valgrind --leak-check=full python app.py
   ```

**解決方案**:
- 定期重啟服務
- 優化代碼中的記憶體使用
- 調整垃圾回收參數
- 升級到更新版本

## 數據問題

### 問題：SIB19 數據不一致

**症狀**:
- 不同事件顯示不同的 SIB19 數據
- 數據更新不同步
- 時間戳不匹配

**診斷步驟**:

1. **檢查數據源**
   ```bash
   # 檢查 SIB19 服務狀態
   curl http://localhost:8000/api/sib19/current
   
   # 驗證數據完整性
   curl http://localhost:8000/api/sib19/validate
   ```

2. **檢查緩存狀態**
   ```python
   # 檢查緩存一致性
   from netstack_api.services.sib19_unified_platform import SIB19UnifiedPlatform
   
   platform = SIB19UnifiedPlatform()
   data = platform.get_current_sib19_data()
   print(f"緩存數據: {data}")
   ```

**解決方案**:
- 清除緩存並重新載入
- 重啟 SIB19 服務
- 檢查數據同步機制
- 驗證數據管理器配置

### 問題：軌道計算錯誤

**症狀**:
- 衛星位置明顯錯誤
- 軌道軌跡不合理
- 計算結果超出預期範圍

**診斷步驟**:

1. **驗證 TLE 數據**
   ```python
   # 檢查 TLE 格式
   def validate_tle(line1, line2):
       # TLE 格式驗證邏輯
       return is_valid
   ```

2. **測試計算精度**
   ```python
   # 與已知結果比較
   known_position = {"lat": 25.0, "lon": 121.0, "alt": 408.0}
   calculated = engine.calculate_position(tle1, tle2, test_time)
   error = calculate_distance(known_position, calculated)
   ```

**解決方案**:
- 更新 TLE 數據源
- 校驗計算算法
- 檢查時間基準設定
- 重新初始化軌道引擎

## 瀏覽器相關問題

### 問題：圖表不顯示

**症狀**:
- 圖表區域空白
- 顯示載入中但從不完成
- 圖表元素錯位

**診斷步驟**:

1. **檢查瀏覽器兼容性**
   - 確認瀏覽器版本支援
   - 檢查 JavaScript 是否啟用
   - 驗證 WebGL 支援

2. **檢查控制台錯誤**
   ```javascript
   // 在瀏覽器控制台執行
   console.log('React version:', React.version);
   console.log('Chart library loaded:', typeof Recharts !== 'undefined');
   ```

**解決方案**:
- 更新瀏覽器到最新版本
- 清除瀏覽器緩存和 Cookie
- 禁用瀏覽器擴展
- 嘗試無痕模式

### 問題：響應式佈局問題

**症狀**:
- 在小螢幕上顯示異常
- 元素重疊或錯位
- 滾動條異常

**解決方案**:
- 調整瀏覽器縮放比例
- 使用建議的螢幕解析度
- 重新整理頁面
- 嘗試不同的瀏覽器

## 緊急恢復程序

### 系統完全無法訪問

1. **立即行動**:
   ```bash
   # 重啟所有服務
   sudo systemctl restart ntn-stack-backend
   sudo systemctl restart ntn-stack-frontend
   sudo systemctl restart postgresql
   sudo systemctl restart redis
   ```

2. **檢查服務狀態**:
   ```bash
   sudo systemctl status ntn-stack-backend
   sudo systemctl status ntn-stack-frontend
   ```

3. **恢復數據庫**:
   ```bash
   # 如果需要，從備份恢復
   pg_restore -d ntn_stack /backup/latest_backup.sql
   ```

### 數據丟失恢復

1. **停止所有寫入操作**
2. **檢查最近的備份**
3. **執行數據恢復程序**
4. **驗證數據完整性**
5. **重新啟動服務**

## 聯繫技術支援

### 何時聯繫支援

- 按照本手冊無法解決問題
- 系統出現安全相關問題
- 數據丟失或損壞
- 需要緊急技術支援

### 提供的資訊

準備以下資訊以加快問題解決：

1. **問題描述**:
   - 具體症狀和錯誤訊息
   - 問題發生的時間
   - 重現步驟

2. **系統資訊**:
   - 作業系統版本
   - 瀏覽器類型和版本
   - 系統配置資訊

3. **日誌文件**:
   - 應用程式日誌
   - 錯誤日誌
   - 系統日誌

4. **螢幕截圖**:
   - 錯誤畫面
   - 控制台輸出
   - 系統狀態

### 聯繫方式

- **緊急支援**: emergency@ntn-stack.com
- **技術支援**: support@ntn-stack.com
- **電話支援**: +886-2-1234-5678 (工作時間)

### 支援等級

- **P1 (緊急)**: 系統完全無法使用 - 4小時內響應
- **P2 (高)**: 核心功能受影響 - 8小時內響應
- **P3 (中)**: 部分功能問題 - 24小時內響應
- **P4 (低)**: 一般問題和建議 - 72小時內響應
