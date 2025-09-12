# 🎓 智慧型 PowerPoint 簡報生成工具

## 📋 工具概覽

本工具集提供基於論文內容的智慧型 PowerPoint 簡報自動生成功能，特別針對學術論文教學簡報優化，具備圖表重要性評估、內容智慧選擇、深度技術解釋等功能。

## 🔧 核心工具

### 🎯 推薦使用 (最新智慧型工具)

#### 1. `create_intelligent_pptx.py` - 智慧型 PowerPoint 生成器 ⭐⭐⭐⭐⭐
**功能**: 整合圖表選擇器，生成高品質教學簡報
- ✅ 自動圖表選擇與整合
- ✅ 中英文混合字體處理 (標楷體 + Times New Roman)
- ✅ 投影片高度自動控制 (20行/頁)
- ✅ 原始圖表精確整合
- ✅ 詳細技術解釋內容

#### 2. `intelligent_figure_selector.py` - 智慧圖表選擇器 ⭐⭐⭐⭐⭐
**功能**: 基於教學價值和技術重要性自動評估並選擇最重要的論文圖表
- ✅ 圖表重要性分析 (1-5 星評級)
- ✅ 教學價值評估
- ✅ 詳細技術說明生成
- ✅ 圖表與內容對應關係建立

### 📚 舊版工具 (Legacy - 保留備用)
- **`create_final_pptx.py`** - 最終優化版本
- **`create_enhanced_pptx_with_images.py`** - 含原始圖表的增強版
- **`create_enhanced_pptx.py`** - 增強版 PowerPoint 生成器  
- **`create_advanced_pptx.py`** - 進階 PowerPoint 生成器
- **`create_optimized_pptx.py`** - 優化版 PowerPoint 生成器
- **`create_pptx_presentation.py`** - 基礎 PowerPoint 生成器

### 🛠️ 輔助工具
- **`extract_pdf_images.py`** - PDF 圖片提取工具
- **`pdf_extraction_summary.json`** - PDF 提取結果摘要
- **`PowerPoint簡報製作技術指南.md`** - 完整技術文檔

## 🚀 快速開始

### 💡 推薦方式 (智慧型生成)
```bash
# 1. 進入工具目錄
cd /home/sat/ntn-stack/tools/powerpoint_generators

# 2. 執行智慧型簡報生成 (推薦!)
python create_intelligent_pptx.py

# 3. 檢查生成結果
ls -la ../../doc/LEO衛星MC-HO演算法智慧簡報.pptx
```

### 📊 圖表重要性評估

#### ⭐⭐⭐⭐⭐ 最高重要性 (必選)
- **Figure 1**: LEO 衛星系統模型 - 建立基礎概念
- **Figure 2**: MC-HO 演算法流程 - 核心技術貢獻  
- **Table 1**: 實驗參數設定 - 可重現性保證

#### ⭐⭐⭐⭐ 高重要性 (強烈建議)
- **Figure 3**: 換手次數性能比較 - 量化效益驗證
- **Figure 4**: 連結失效分析 - 可靠性評估

#### ⭐⭐⭐ 中等重要性 (可選)
- **Figure 5**: 時間序列分析 - 動態行為研究
- **Figure 6**: 系統容量分析 - 頻譜效率權衡

## 🎯 智慧型生成特色

### ✅ 技術完整性
- 🛰️ LEO 衛星系統架構說明
- 🔄 MC-HO 演算法完整流程
- 📊 實驗參數與環境設定
- 📈 性能比較與驗證結果

### ✅ 教學適用性
- 📚 由淺入深的邏輯結構
- 🎯 重點突出的內容組織
- 🖼️ 圖文並茂的視覺呈現
- 💡 詳細的技術解釋

### ✅ 視覺品質
- 🎨 標準學術簡報格式
- 🔤 中英文混合字體處理
- 📏 投影片高度自動控制
- 🖼️ 高品質原始圖表整合

## 📁 輸出檔案

### 🎯 智慧型生成輸出
- `LEO衛星MC-HO演算法智慧簡報.pptx` - **最終簡報檔案** (推薦使用)
- `智慧簡報創建報告.md` - 詳細創建報告與品質指標

### 📊 分析與選擇結果
- `intelligent_figure_selection.json` - 圖表選擇與重要性分析
- `pdf_extraction_summary.json` - PDF 圖片提取分析摘要

### 🎓 使用場景

#### 👨‍🏫 學術教學
- 研究生課程教學簡報
- 論文技術細節講解
- 學術會議報告準備

#### 👨‍💼 技術分享  
- 企業內部技術分享
- 工程團隊培訓
- 產品技術說明

#### 📚 研究展示
- 學位論文答辯
- 研究進度報告
- 技術評審簡報

## 🔧 自定義使用

### 圖表數量調整
```python
from intelligent_figure_selector import IntelligentFigureSelector

selector = IntelligentFigureSelector()
# 選擇 3 個最重要的圖表
selected_figures = selector.select_figures_by_priority(max_figures=3)
```

### 投影片格式調整
```python
from create_intelligent_pptx import IntelligentPowerPointGenerator

generator = IntelligentPowerPointGenerator()
# 調整每頁最大行數
generator.max_lines_per_slide = 25
generator.generate_intelligent_presentation()
```

## 💡 最佳實務

### 🎯 使用建議
1. **優先使用智慧型生成器**: 自動選擇最重要圖表，避免資訊過載
2. **檢查圖片路徑**: 確認論文圖片已正確提取
3. **驗證模板存在**: 確認模板檔案路徑正確
4. **定制化調整**: 根據聽眾背景調整技術深度

### ⚠️ 常見問題
- **路徑問題**: 檢查相對路徑是否正確
- **字體問題**: 確認系統已安裝標楷體
- **圖片缺失**: 驗證 PDF 圖片提取成功

## 🔧 維護資訊

- **最新更新**: 2024-09-06 - 智慧型生成器完成
- **來源**: 專案根目錄遷移
- **用途**: 學術論文教學簡報自動生成
- **技術棧**: python-pptx + 智慧圖表分析

---

## 📞 更多資源

### 📚 技術文檔
- 📁 `PowerPoint簡報製作技術指南.md` - **完整技術實現指南**
- 📁 `項目記憶與案例文檔.md` - **實際項目案例與經驗記憶**

### 🎯 實際案例
- **TLE教學系列**: 8階段127張投影片完整案例
- **六階段處理系統**: 14張投影片濃縮概覽案例  
- **關鍵經驗**: 8000→0顆可見問題解決、時間基準選擇等

**🎉 現在開始享受智慧化的學術簡報製作體驗！**