# TLE 數據時間基準重要說明

## 🚨 關鍵原則
前端渲染衛星位置時，**必須使用 TLE 文件的日期作為時間基準**，而非當前系統時間。

## ✅ 正確實作方式
```javascript
// 從後端數據獲取 TLE 時間信息
const satelliteData = await fetch('/api/satellites/data');
const tleDate = satelliteData.tle_source_date; // "20250816"
const tleEpoch = satelliteData.tle_epoch_time; // TLE epoch 時間

// 使用 TLE 日期作為動畫基準時間
const baseTime = new Date(
  parseInt(tleDate.substr(0,4)),   // 年
  parseInt(tleDate.substr(4,2))-1,  // 月(從0開始)
  parseInt(tleDate.substr(6,2))     // 日
);

// 所有軌道計算都基於這個時間
const currentPosition = calculatePosition(baseTime, elapsedSeconds);
```

## ❌ 錯誤實作方式
```javascript
// 絕對不要使用當前系統時間！
const wrongTime = new Date();  // ❌ 錯誤
const wrongTime2 = Date.now(); // ❌ 錯誤
```

## ⚠️ 影響說明
使用錯誤的時間基準會導致：
- 衛星位置偏差數百公里
- 可見性判斷完全錯誤
- 覆蓋率分析失真
- 換手決策時機錯誤

## 🔍 檢查要點
1. 確認後端 API 返回包含 `tle_source_date` 欄位
2. 前端動畫時間軸以 TLE 日期為起點
3. 所有 SGP4 計算使用 TLE Epoch 時間
4. 不要使用 `processing_timestamp` 進行位置計算

