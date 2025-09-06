# PowerPoint 簡報製作技術指南
## 基於 python-pptx 的專業簡報開發流程

---

## 📋 目錄
1. [環境準備與套件安裝](#環境準備與套件安裝)
2. [智慧圖表選擇與重要性評估](#智慧圖表選擇與重要性評估)
3. [投影片高度控制技術](#投影片高度控制技術)
4. [中英文字體混合設定](#中英文字體混合設定)
5. [內容分頁機制](#內容分頁機制)
6. [PDF 圖片與表格提取技術](#pdf-圖片與表格提取技術)
7. [智慧型 PowerPoint 生成器](#智慧型-powerpoint-生成器)
8. [模板處理與版型設定](#模板處理與版型設定)
9. [完整程式碼範例](#完整程式碼範例)
10. [最佳實務與注意事項](#最佳實務與注意事項)
11. [故障排除指南](#故障排除指南)

---

## 🚀 環境準備與套件安裝

### 1. 虛擬環境建立 (強制必要)
```bash
# 創建 Python 虛擬環境
python3 -m venv pptx_env

# 啟用虛擬環境 (每次使用前必須執行)
source pptx_env/bin/activate

# 驗證虛擬環境啟用
which python  # 應顯示 pptx_env/bin/python
```

### 2. 核心套件安裝
```bash
# 安裝 python-pptx 及相依套件
pip install python-pptx

# 驗證安裝成功
python -c "from pptx import Presentation; print('python-pptx 安裝成功')"
```

### 3. 相依套件清單
```
python-pptx==1.0.2
Pillow>=3.3.2          # 圖片處理
XlsxWriter>=0.5.7      # Excel 相容性
lxml>=3.1.0            # XML 處理
typing-extensions>=4.9.0  # 類型提示支援
```

---

## 🧠 智慧圖表選擇與重要性評估

### 1. 圖表重要性分析框架

#### 評估維度設計
```python
class FigureImportanceFramework:
    """圖表重要性評估框架"""
    
    def __init__(self):
        self.evaluation_criteria = {
            "teaching_value": {
                "concept_building": "是否有助於建立基礎概念",
                "technical_depth": "是否包含關鍵技術細節",
                "verification_effect": "是否提供量化性能數據",
                "practical_value": "是否具備工程應用價值"
            },
            "technical_importance": {
                "core_algorithm": "是否展示核心演算法",
                "system_architecture": "是否說明系統架構",
                "performance_analysis": "是否進行性能分析",
                "experimental_validation": "是否提供實驗驗證"
            }
        }
        
    def calculate_priority(self, figure_info):
        """計算圖表優先級"""
        priority_mapping = {
            (5, 5): 1,  # 最高重要性
            (5, 4): 1,  # 最高重要性
            (4, 5): 1,  # 最高重要性
            (4, 4): 2,  # 高重要性
            (4, 3): 2,  # 高重要性
            (3, 4): 2,  # 高重要性
            (3, 3): 3   # 中等重要性
        }
        
        key = (figure_info['teaching_value'], figure_info['technical_importance'])
        return priority_mapping.get(key, 3)
```

#### 圖表分類標準
```python
# ⭐⭐⭐⭐⭐ 最高重要性 (必須包含)
CRITICAL_FIGURES = {
    "基礎概念圖": "建立系統模型的基本理解",
    "核心演算法圖": "展示技術貢獻的關鍵流程",
    "實驗參數表": "確保結果可重現性"
}

# ⭐⭐⭐⭐ 高重要性 (強烈建議)
HIGH_PRIORITY_FIGURES = {
    "性能比較圖": "量化展示演算法優勢",
    "可靠性分析圖": "驗證系統穩定性"
}

# ⭐⭐⭐ 中等重要性 (可選擇性包含)
MEDIUM_PRIORITY_FIGURES = {
    "時域分析圖": "展示動態行為特性",
    "容量分析圖": "說明系統權衡考量"
}
```

### 2. 智慧圖表選擇演算法

#### 核心選擇邏輯
```python
def intelligent_figure_selection(all_figures, max_count=5, teaching_focus="comprehensive"):
    """智慧圖表選擇演算法"""
    
    # Step 1: 重要性評估
    scored_figures = []
    for figure in all_figures:
        score = calculate_comprehensive_score(figure, teaching_focus)
        scored_figures.append((figure, score))
    
    # Step 2: 按分數排序
    sorted_figures = sorted(scored_figures, key=lambda x: x[1], reverse=True)
    
    # Step 3: 確保教學完整性
    selected_figures = ensure_teaching_completeness(sorted_figures[:max_count])
    
    # Step 4: 驗證選擇結果
    validate_selection_quality(selected_figures)
    
    return selected_figures

def calculate_comprehensive_score(figure, teaching_focus):
    """計算圖表綜合得分"""
    base_score = figure['priority'] * 10 + figure['teaching_value'] * 2
    
    # 根據教學重點調整權重
    if teaching_focus == "fundamental":
        if figure['type'] in ['system_model', 'algorithm_flow']:
            base_score += 5
    elif teaching_focus == "performance":
        if figure['type'] in ['performance_comparison', 'reliability_analysis']:
            base_score += 5
    
    return base_score
```

### 3. 詳細技術說明生成

#### 說明內容結構化
```python
def generate_figure_explanation(figure_name, figure_type):
    """為圖表生成結構化的技術說明"""
    
    explanation_template = {
        "title": f"{figure_name} 技術解析",
        "overview": "圖表概述與重要性",
        "key_concepts": [],
        "technical_details": [],
        "teaching_focus": "",
        "practical_insights": []
    }
    
    if figure_type == "system_model":
        return generate_system_model_explanation(figure_name)
    elif figure_type == "algorithm_flow":
        return generate_algorithm_explanation(figure_name)
    elif figure_type == "performance_analysis":
        return generate_performance_explanation(figure_name)

def generate_system_model_explanation(figure_name):
    """生成系統模型圖表說明"""
    return {
        "overview": "LEO 衛星系統覆蓋模型與基礎架構",
        "key_concepts": [
            "LEO 衛星軌道特性 (高度、速度、覆蓋)",
            "多重覆蓋區域 (Multi-coverage Area) 概念",
            "衛星移動性對網路的影響",
            "與 GEO/MEO 衛星的差異比較"
        ],
        "technical_details": [
            "軌道高度：600km（相對於 GEO 的 35,786km）",
            "運行速度：7.56km/s（高速移動特性）",
            "波束直徑：50km（相對較小的覆蓋範圍）",
            "延遲特性：~2.5ms（大幅優於 GEO 的 ~250ms）"
        ],
        "teaching_focus": "建立 LEO 衛星網路的基本概念，理解多重覆蓋區域如何形成 MC-HO 的技術基礎",
        "practical_insights": [
            "低延遲特性適合即時應用",
            "高速移動需要頻繁切換管理",
            "多重覆蓋提供 Soft Handover 機會",
            "相對較小覆蓋需要更密集的星座"
        ]
    }
```

### 4. 教學邏輯完整性檢查

#### 邏輯流程驗證
```python
def validate_teaching_logic(selected_figures):
    """驗證選中圖表的教學邏輯完整性"""
    
    required_components = {
        "foundation": False,      # 基礎概念建立
        "core_technology": False, # 核心技術說明
        "experimental_setup": False, # 實驗設置
        "performance_validation": False, # 性能驗證
        "conclusion": False       # 結論總結
    }
    
    for figure in selected_figures:
        if figure['type'] == 'system_model':
            required_components['foundation'] = True
        elif figure['type'] == 'algorithm_flow':
            required_components['core_technology'] = True
        elif figure['type'] == 'parameter_table':
            required_components['experimental_setup'] = True
        elif figure['type'] in ['performance_comparison', 'reliability_analysis']:
            required_components['performance_validation'] = True
    
    # 檢查完整性
    completeness_score = sum(required_components.values()) / len(required_components)
    
    if completeness_score < 0.8:
        print("⚠️  教學邏輯不完整，建議增加基礎或驗證內容")
    
    return completeness_score, required_components

def ensure_teaching_completeness(sorted_figures):
    """確保教學內容的完整性"""
    
    selected = []
    essential_types = ['system_model', 'algorithm_flow', 'parameter_table']
    
    # 優先選擇必要類型
    for essential_type in essential_types:
        for figure, score in sorted_figures:
            if figure['type'] == essential_type and figure not in selected:
                selected.append(figure)
                break
    
    # 填充其他高分圖表
    for figure, score in sorted_figures:
        if figure not in selected and len(selected) < 5:
            selected.append(figure)
    
    return selected
```

### 5. 實際應用範例

#### LEO 衛星 MC-HO 論文圖表分析
```python
# 實際圖表重要性評估結果
leo_figures_analysis = {
    "Figure 1": {
        "description": "LEO 衛星覆蓋場景圖",
        "priority": 1,  # 最高
        "teaching_value": 5,
        "key_concepts": [
            "Multi-coverage 重疊區域概念",
            "衛星運動與覆蓋範圍變化",
            "LEO 衛星星座架構"
        ],
        "selection_reason": "建立 LEO 衛星網路基本概念的核心圖表"
    },
    
    "Figure 2": {
        "description": "MC-HO 演算法流程圖",
        "priority": 1,  # 最高
        "teaching_value": 5,
        "key_concepts": [
            "Master Node (MN) 與 Secondary Node (SN) 架構",
            "Packet Duplication 機制",
            "條件式切換 (CHO) 觸發條件"
        ],
        "selection_reason": "展示論文核心技術貢獻的關鍵圖表"
    },
    
    "Figure 3": {
        "description": "平均換手次數比較",
        "priority": 2,  # 高
        "teaching_value": 4,
        "quantitative_data": "40% overlap: SC-HO 247 vs MC-HO 130 HOs/s",
        "selection_reason": "量化驗證 MC-HO 相對於 SC-HO 的性能優勢"
    }
}

# 自動選擇結果
selected_figures = intelligent_figure_selection(leo_figures_analysis, max_count=5)
print("🎯 智慧選擇結果:")
for i, figure in enumerate(selected_figures, 1):
    print(f"{i}. {figure['description']} (優先級: {figure['priority']})")
```

---

## 📏 投影片高度控制技術

### 1. 投影片尺寸規格
```python
# PowerPoint 16:9 標準尺寸
SLIDE_WIDTH = Inches(10)    # 10 英吋
SLIDE_HEIGHT = Inches(7.5)  # 7.5 英吋

# 內容區域計算 (扣除標題和邊距)
CONTENT_TOP = Inches(1.2)     # 標題下方起始位置
CONTENT_BOTTOM = Inches(7.2)  # 底部邊距
CONTENT_HEIGHT = CONTENT_BOTTOM - CONTENT_TOP  # 實際可用高度 = 6 英吋
```

### 2. 字型與行高計算
```python
def calculate_content_limits():
    """計算每頁最大行數限制"""
    # 字型規格
    FONT_SIZE = 14          # 14pt 字型大小
    LINE_HEIGHT_RATIO = 1.2 # 行距比例 (字型大小 × 1.2)
    
    # 行高計算
    line_height_pt = FONT_SIZE * LINE_HEIGHT_RATIO  # 16.8pt
    
    # 可用內容高度轉換為 pt (1 inch = 72 pt)
    content_height_pt = 6 * 72  # 432 pt
    
    # 最大行數計算 (保守估計)
    max_lines = int(content_height_pt / line_height_pt)  # ≈ 25 行
    safe_max_lines = max_lines - 3  # 保留安全邊距 = 22 行
    
    return safe_max_lines
```

### 3. 內容長度估算函數
```python
def estimate_content_lines(content_text):
    """精確估算內容所需行數"""
    lines = content_text.split('\n')
    total_lines = 0
    
    for line in lines:
        if not line.strip():  # 空行
            total_lines += 1
        else:
            # 長行自動換行計算 (每行最多 80 字符)
            char_count = len(line)
            estimated_lines = max(1, (char_count + 79) // 80)
            total_lines += estimated_lines
    
    return total_lines
```

### 4. 自動分頁機制
```python
def split_long_content(content_text, max_lines=20):
    """將過長內容自動分頁"""
    if estimate_content_lines(content_text) <= max_lines:
        return [content_text]
    
    lines = content_text.split('\n')
    parts = []
    current_part = []
    current_lines = 0
    
    for line in lines:
        line_count = max(1, (len(line) + 79) // 80) if line.strip() else 1
        
        if current_lines + line_count > max_lines and current_part:
            # 當前頁面已滿，開始新頁面
            parts.append('\n'.join(current_part))
            current_part = [line]
            current_lines = line_count
        else:
            current_part.append(line)
            current_lines += line_count
    
    # 添加最後一個頁面
    if current_part:
        parts.append('\n'.join(current_part))
    
    return parts
```

---

## 🔤 中英文字體混合設定

### 1. 字體設定核心函數
```python
import re
from pptx.util import Pt

def set_mixed_font_style(text_frame, chinese_font="標楷體", english_font="Times New Roman", font_size=14):
    """設置混合中英文字體 - 逐字符精確處理"""
    for paragraph in text_frame.paragraphs:
        text = paragraph.text
        if text:
            # 清除現有格式
            paragraph.clear()
            
            # 逐字符分析並設置對應字體
            i = 0
            while i < len(text):
                char = text[i]
                # 英文字符正規表達式 (包含數字、標點、符號)
                if re.match(r'[a-zA-Z0-9\s\-_.,()[\]/+=<>&%]', char):
                    # 收集連續的英文字符
                    j = i
                    while j < len(text) and re.match(r'[a-zA-Z0-9\s\-_.,()[\]/+=<>&%]', text[j]):
                        j += 1
                    run = paragraph.add_run()
                    run.text = text[i:j]
                    run.font.name = english_font
                    run.font.size = Pt(font_size)
                    i = j
                else:
                    # 收集連續的中文字符
                    j = i
                    while j < len(text) and not re.match(r'[a-zA-Z0-9\s\-_.,()[\]/+=<>&%]', text[j]):
                        j += 1
                    run = paragraph.add_run()
                    run.text = text[i:j]
                    run.font.name = chinese_font
                    run.font.size = Pt(font_size)
                    i = j
```

### 2. 字體設定最佳實務
```python
# 字體大小建議
FONT_SIZES = {
    'title': 22,      # 標題
    'subtitle': 18,   # 副標題
    'content': 15,    # 一般內容
    'small': 13,      # 小字內容
    'code': 12        # 程式碼
}

# 中文字體備選方案
CHINESE_FONTS = [
    "標楷體",           # 首選
    "DFKai-SB",        # Windows 標楷體
    "BiauKai",         # Linux 標楷體
    "SimSun",          # 備選方案
]

# 英文字體備選方案
ENGLISH_FONTS = [
    "Times New Roman", # 首選
    "Times",           # macOS
    "Liberation Serif", # Linux
    "DejaVu Serif",    # 備選方案
]
```

### 3. 字符分類詳細規則
```python
# 英文字符範圍 (使用 Times New Roman)
ENGLISH_PATTERNS = [
    r'[a-zA-Z]',           # 英文字母
    r'[0-9]',              # 阿拉伯數字
    r'[\s]',               # 空格
    r'[\-_.,()[\]/]',      # 常用標點
    r'[+=<>&%]',           # 數學符號
    r'[:;!?]',             # 其他標點
]

# 中文字符 (使用標楷體)
# 所有不符合英文規則的字符，包括：
# - 中文漢字
# - 中文標點符號（，。？！）
# - 全形符號
# - 特殊符號
```

---

## 📄 內容分頁機制

### 1. 分頁策略設計
```python
def create_multi_slide_content(prs, title_base, content_parts, layout):
    """創建多頁內容投影片"""
    slides = []
    
    for i, content_part in enumerate(content_parts):
        # 生成頁面標題
        if len(content_parts) > 1:
            slide_title = f"{title_base} ({i+1}/{len(content_parts)})"
        else:
            slide_title = title_base
        
        # 創建投影片
        slide = prs.slides.add_slide(layout)
        slide.shapes.title.text = slide_title
        slide.placeholders[1].text = content_part
        
        # 設置字體
        set_mixed_font_style(slide.shapes.title.text_frame, font_size=18)
        set_mixed_font_style(slide.placeholders[1].text_frame, font_size=14)
        
        slides.append(slide)
    
    return slides
```

### 2. 智慧分頁演算法
```python
def smart_content_split(content_sections, max_lines_per_slide=20):
    """智慧內容分頁演算法"""
    result_pages = []
    current_page = []
    current_lines = 0
    
    for section in content_sections:
        section_lines = estimate_content_lines(section)
        
        # 檢查是否需要新頁面
        if current_lines + section_lines > max_lines_per_slide and current_page:
            # 完成當前頁面
            result_pages.append('\n\n'.join(current_page))
            current_page = [section]
            current_lines = section_lines
        else:
            current_page.append(section)
            current_lines += section_lines
    
    # 處理最後一頁
    if current_page:
        result_pages.append('\n\n'.join(current_page))
    
    return result_pages
```

---

## 🖼️ PDF 圖片與表格提取技術

### 1. 環境準備與套件安裝
```bash
# 在已啟用的虛擬環境中安裝 PDF 處理套件
pip install PyMuPDF pdf2image Pillow

# 驗證安裝
python -c "import fitz; print('PyMuPDF 安裝成功')"
python -c "from pdf2image import convert_from_path; print('pdf2image 安裝成功')"
```

### 2. PDF 圖片提取核心函數
```python
import fitz  # PyMuPDF
import json
import os
from pdf2image import convert_from_path

def extract_images_from_pdf(pdf_path, output_dir="論文圖片"):
    """從 PDF 中提取所有圖片"""
    
    # 創建輸出目錄
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 開啟 PDF 文件
    pdf_document = fitz.open(pdf_path)
    extracted_images = []
    
    print(f"📖 開始處理 PDF: {pdf_path}")
    print(f"📄 總頁數: {len(pdf_document)}")
    
    # 遍歷每一頁
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        print(f"🔍 處理第 {page_num + 1} 頁...")
        
        # 獲取頁面中的所有圖片
        image_list = page.get_images(full=True)
        print(f"   發現 {len(image_list)} 張圖片")
        
        # 提取每張圖片
        for img_index, img in enumerate(image_list):
            xref = img[0]  # 圖片的 xref 編號
            
            try:
                # 提取圖片數據
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # 生成檔案名稱
                filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                filepath = os.path.join(output_dir, filename)
                
                # 儲存圖片
                with open(filepath, "wb") as img_file:
                    img_file.write(image_bytes)
                
                # 獲取圖片尺寸
                width = base_image["width"]
                height = base_image["height"]
                
                extracted_images.append({
                    "page": page_num + 1,
                    "image_index": img_index + 1,
                    "filename": filename,
                    "width": width,
                    "height": height,
                    "path": os.path.join(output_dir, filename)
                })
                
                print(f"   ✅ 提取成功: {filename} ({width}x{height})")
                
            except Exception as e:
                print(f"   ❌ 提取失敗: {e}")
    
    # 關閉 PDF 文件
    pdf_document.close()
    
    # 儲存提取資訊
    info_file = os.path.join(output_dir, "extraction_info.json")
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_images, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 提取完成:")
    print(f"   總計提取 {len(extracted_images)} 張圖片")
    print(f"   圖片儲存至: {output_dir}")
    print(f"   詳細資訊: {info_file}")
    
    return extracted_images
```

### 3. PDF 頁面轉圖片功能
```python
def convert_pdf_pages_to_images(pdf_path, output_dir="論文頁面", dpi=300):
    """將 PDF 每頁轉換為高解析度圖片"""
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        # 轉換 PDF 頁面為圖片
        print(f"🔄 轉換 PDF 頁面為圖片 (DPI: {dpi})...")
        pages = convert_from_path(pdf_path, dpi=dpi)
        
        page_images = []
        for i, page in enumerate(pages):
            filename = f"page_{i + 1}_high_res.png"
            filepath = os.path.join(output_dir, filename)
            
            # 儲存高解析度圖片
            page.save(filepath, 'PNG')
            
            page_images.append({
                "page": i + 1,
                "filename": filename,
                "width": page.width,
                "height": page.height,
                "path": filepath
            })
            
            print(f"   ✅ 頁面 {i + 1}: {filename} ({page.width}x{page.height})")
        
        print(f"\n📊 頁面轉換完成: {len(page_images)} 頁")
        return page_images
        
    except Exception as e:
        print(f"❌ 頁面轉換失敗: {e}")
        return []
```

### 4. 論文圖表識別功能
```python
def identify_figures_and_tables(pdf_path):
    """識別 PDF 中的圖表位置和類型"""
    
    pdf_document = fitz.open(pdf_path)
    figures_and_tables = []
    
    print("🔍 識別論文中的圖表...")
    
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text = page.get_text()
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # 識別圖表關鍵字
            if any(keyword in line.lower() for keyword in ['fig.', 'figure', '圖']):
                figures_and_tables.append({
                    "page": page_num + 1,
                    "line": line_num,
                    "text": line[:50] + "..." if len(line) > 50 else line,
                    "type": "Figure"
                })
            elif any(keyword in line.lower() for keyword in ['table', 'tab.', '表']):
                figures_and_tables.append({
                    "page": page_num + 1,
                    "line": line_num,
                    "text": line[:50] + "..." if len(line) > 50 else line,
                    "type": "Table"
                })
    
    pdf_document.close()
    
    print(f"📋 識別到 {len(figures_and_tables)} 個圖表引用")
    return figures_and_tables
```

### 5. 完整 PDF 分析與提取流程
```python
def comprehensive_pdf_extraction(pdf_path):
    """完整的 PDF 圖表提取分析流程"""
    
    print("🚀 開始完整 PDF 圖表提取流程")
    print("=" * 50)
    
    # 1. 提取 PDF 中的圖片
    extracted_images = extract_images_from_pdf(pdf_path, "論文圖片")
    
    # 2. 轉換 PDF 頁面為圖片
    page_images = convert_pdf_pages_to_images(pdf_path, "論文頁面")
    
    # 3. 識別論文中的圖表
    figures_and_tables = identify_figures_and_tables(pdf_path)
    
    # 4. 生成綜合分析報告
    analysis_report = {
        "pdf_file": os.path.basename(pdf_path),
        "figures_and_tables": figures_and_tables,
        "extracted_images": extracted_images,
        "page_images": page_images,
        "timestamp": "2024-09-06"
    }
    
    # 5. 儲存分析報告
    with open("pdf_extraction_summary.json", 'w', encoding='utf-8') as f:
        json.dump(analysis_report, f, ensure_ascii=False, indent=2)
    
    print("\n📊 完整提取分析報告:")
    print(f"   • 識別圖表引用: {len(figures_and_tables)} 個")
    print(f"   • 提取圖片: {len(extracted_images)} 張")  
    print(f"   • 頁面圖片: {len(page_images)} 張")
    print(f"   • 分析報告: pdf_extraction_summary.json")
    print("=" * 50)
    
    return analysis_report

# 使用範例
if __name__ == "__main__":
    pdf_file = "research_paper.pdf"
    comprehensive_pdf_extraction(pdf_file)
```

### 6. 簡報圖片整合功能
```python
def add_image_to_slide(slide, image_path, left=None, top=None, width=None, height=None):
    """將提取的圖片添加到投影片中"""
    
    try:
        # 預設圖片位置和大小
        if left is None:
            left = Inches(6.5)  # 右側位置
        if top is None:
            top = Inches(1.5)   # 標題下方
        if width is None:
            width = Inches(3)   # 預設寬度
        if height is None:
            height = Inches(2.5) # 預設高度
        
        # 添加圖片到投影片
        picture = slide.shapes.add_picture(image_path, left, top, width, height)
        print(f"✅ 圖片已添加: {os.path.basename(image_path)}")
        
        return picture
        
    except Exception as e:
        print(f"❌ 圖片添加失敗: {e}")
        return None

def integrate_pdf_images_to_presentation(prs, image_mapping):
    """將 PDF 提取的圖片整合到簡報中"""
    
    print("🖼️ 開始整合 PDF 圖片到簡報...")
    
    for slide_info in image_mapping:
        slide_index = slide_info["slide_index"]
        image_path = slide_info["image_path"]
        
        if slide_index < len(prs.slides):
            slide = prs.slides[slide_index]
            add_image_to_slide(slide, image_path)
            print(f"   投影片 {slide_index + 1}: 已添加 {os.path.basename(image_path)}")
    
    print("✅ PDF 圖片整合完成")
```

### 7. 圖片品質優化
```python
def optimize_extracted_images(image_dir, max_width=1920, max_height=1080):
    """優化提取的圖片品質和大小"""
    
    from PIL import Image
    
    print(f"🔧 優化圖片品質 (最大尺寸: {max_width}x{max_height})...")
    
    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(image_dir, filename)
            
            try:
                with Image.open(filepath) as img:
                    # 檢查是否需要調整大小
                    if img.width > max_width or img.height > max_height:
                        # 計算等比例縮放
                        ratio = min(max_width / img.width, max_height / img.height)
                        new_width = int(img.width * ratio)
                        new_height = int(img.height * ratio)
                        
                        # 調整圖片大小
                        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        resized_img.save(filepath, optimize=True, quality=95)
                        
                        print(f"   ✅ 優化: {filename} ({img.width}x{img.height} → {new_width}x{new_height})")
                    else:
                        print(f"   ⏭️  跳過: {filename} (尺寸適當)")
                        
            except Exception as e:
                print(f"   ❌ 處理失敗: {filename} - {e}")
```

---

## 🤖 智慧型 PowerPoint 生成器

### 1. 整合架構設計

#### 智慧型生成器核心組件
```python
class IntelligentPowerPointGenerator:
    """智慧型 PowerPoint 生成器，整合圖表分析功能"""
    
    def __init__(self, template_path="../../doc/template.pptx"):
        self.template_path = template_path
        self.max_lines_per_slide = 20
        self.figure_selector = IntelligentFigureSelector()
        
        # 圖片資源路徑
        self.image_base_path = "../../論文圖片"
        
        # 字型設定
        self.chinese_font = "標楷體"
        self.english_font = "Times New Roman"
    
    def generate_intelligent_presentation(self, output_filename="智慧簡報.pptx"):
        """生成智慧型簡報的完整流程"""
        
        print("🚀 開始生成智慧型 PowerPoint 簡報...")
        
        # 1. 載入模板
        prs = self.load_template()
        
        # 2. 智慧選擇重要圖表
        selected_figures = self.figure_selector.select_figures_by_priority(max_figures=5)
        explanations = self.figure_selector.generate_figure_explanations(selected_figures)
        
        # 3. 創建投影片內容
        self.create_title_slide(prs)
        self.create_figure_slides(prs, selected_figures, explanations)
        self.create_conclusion_slide(prs)
        
        # 4. 儲存簡報
        prs.save(output_filename)
        
        # 5. 生成品質報告
        self.generate_creation_report(selected_figures, len(prs.slides))
        
        return prs
```

### 2. 智慧內容生成流程

#### 投影片內容自動化創建
```python
def create_figure_slides(self, prs, selected_figures, explanations):
    """根據選中的重要圖表創建投影片"""
    
    for figure_info in selected_figures:
        figure_name = figure_info['figure_name']
        description = figure_info['description']
        image_file = figure_info['image_file']
        
        # 獲取詳細說明內容
        explanation = explanations.get(figure_name, "")
        
        # 分割內容以適應投影片高度
        content_lines = explanation.split('\n')
        slides_content = self.split_content_for_slides(content_lines, self.max_lines_per_slide)
        
        for i, slide_content in enumerate(slides_content):
            slide_layout = prs.slide_layouts[1]  # 標題與內容版面
            slide = prs.slides.add_slide(slide_layout)
            
            # 設定標題
            if len(slides_content) > 1:
                title_text = f"{figure_name}: {description} ({i+1}/{len(slides_content)})"
            else:
                title_text = f"{figure_name}: {description}"
            
            slide.shapes.title.text = title_text
            self.set_mixed_font_style(slide.shapes.title.text_frame, font_size=20)
            
            # 設定內容
            if len(slide.placeholders) > 1:
                content_placeholder = slide.placeholders[1]
                content_text = '\n'.join(slide_content)
                content_placeholder.text = content_text
                self.set_mixed_font_style(content_placeholder.text_frame, font_size=14)
            
            # 在第一張投影片添加圖片 (如果存在)
            if i == 0 and image_file:
                image_path = self.find_image_path(image_file)
                if image_path:
                    self.add_image_to_slide(slide, image_path)

def find_image_path(self, image_file):
    """智慧尋找圖片檔案路徑"""
    possible_paths = [
        os.path.join(self.image_base_path, image_file),
        f"../../論文圖片/{image_file}",
        f"論文圖片/{image_file}",
        image_file
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    print(f"⚠️  圖片未找到: {image_file}")
    return None
```

### 3. 品質控制與驗證

#### 自動品質檢查系統
```python
def validate_presentation_quality(self, prs, selected_figures):
    """驗證簡報品質"""
    
    quality_metrics = {
        "slide_count": len(prs.slides),
        "figure_integration": 0,
        "content_completeness": 0,
        "teaching_logic": 0
    }
    
    # 檢查圖表整合情況
    images_found = 0
    for figure in selected_figures:
        if figure['image_file'] and self.find_image_path(figure['image_file']):
            images_found += 1
    
    quality_metrics["figure_integration"] = images_found / len(selected_figures)
    
    # 檢查教學邏輯完整性
    completeness_score, components = self.validate_teaching_logic(selected_figures)
    quality_metrics["content_completeness"] = completeness_score
    
    # 總體品質評分
    overall_quality = (
        quality_metrics["figure_integration"] * 0.3 +
        quality_metrics["content_completeness"] * 0.4 +
        (1.0 if quality_metrics["slide_count"] >= 8 else 0.8) * 0.3
    )
    
    return quality_metrics, overall_quality

def generate_creation_report(self, selected_figures, total_slides):
    """生成簡報創建報告"""
    
    quality_metrics, overall_quality = self.validate_presentation_quality(
        prs, selected_figures
    )
    
    report = f"""# 📊 智慧型 PowerPoint 簡報創建報告

## 🎯 簡報概覽
- **總投影片數**: {total_slides} 張
- **核心技術圖表**: {len(selected_figures)} 個
- **整體品質評分**: {overall_quality:.2%}
- **創建時間**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📋 圖表選擇結果
"""
    
    for i, fig in enumerate(selected_figures, 1):
        priority_stars = "⭐" * fig['teaching_value']
        report += f"""### {i}. {fig['figure_name']}
- **教學價值**: {priority_stars}
- **說明**: {fig['description']}
- **圖片整合**: {'✅ 成功' if fig['image_file'] else '⚠️ 需手動添加'}

"""
    
    report += f"""## 📈 品質指標
- **圖表整合率**: {quality_metrics['figure_integration']:.1%}
- **內容完整性**: {quality_metrics['content_completeness']:.1%}
- **教學邏輯性**: {'✅ 完整' if quality_metrics['content_completeness'] >= 0.8 else '⚠️ 待改進'}

## ✅ 相比傳統方法的優勢
- **有針對性**: 智慧選擇最重要圖表，避免資訊過載
- **有深度**: 每個圖表配有詳細技術解釋
- **有邏輯**: 完整的教學流程設計
- **有品質**: 自動品質檢查與最佳化
"""
    
    return report
```

### 4. 使用方式與最佳實務

#### 快速使用範例
```python
# 基本使用方式
def main():
    generator = IntelligentPowerPointGenerator()
    
    # 生成智慧簡報
    presentation = generator.generate_intelligent_presentation(
        output_filename="LEO衛星MC-HO演算法智慧簡報.pptx"
    )
    
    print(f"✅ 簡報生成完成，包含 {len(presentation.slides)} 張投影片")

# 自定義配置
def advanced_usage():
    generator = IntelligentPowerPointGenerator(
        template_path="custom_template.pptx"
    )
    
    # 調整參數
    generator.max_lines_per_slide = 25
    generator.chinese_font = "微軟正黑體"
    
    # 指定圖表選擇重點
    generator.figure_selector.teaching_focus = "performance"
    
    # 生成簡報
    presentation = generator.generate_intelligent_presentation()
```

#### 品質優化建議
```python
# 品質最佳化配置
QUALITY_OPTIMIZATION_CONFIG = {
    "max_figures": 5,           # 最多5個圖表，避免資訊過載
    "max_lines_per_slide": 20,  # 每頁最多20行，確保可讀性
    "min_teaching_value": 4,    # 最低教學價值4星，確保品質
    "require_core_concepts": True, # 必須包含核心概念圖表
    "balance_priorities": True,    # 平衡不同優先級的圖表
}

def optimize_figure_selection(figures, config):
    """優化圖表選擇策略"""
    
    # 確保包含核心概念
    if config["require_core_concepts"]:
        core_types = ['system_model', 'algorithm_flow', 'parameter_table']
        selected = ensure_core_types_included(figures, core_types)
    
    # 過濾低價值圖表
    if config["min_teaching_value"]:
        selected = [f for f in selected if f['teaching_value'] >= config["min_teaching_value"]]
    
    # 平衡優先級
    if config["balance_priorities"]:
        selected = balance_priority_distribution(selected, config["max_figures"])
    
    return selected[:config["max_figures"]]
```

### 5. 擴展與定制化

#### 支援不同領域的論文
```python
class DomainSpecificGenerator(IntelligentPowerPointGenerator):
    """領域特定的簡報生成器"""
    
    def __init__(self, domain="satellite_communication"):
        super().__init__()
        self.domain = domain
        self.load_domain_config()
    
    def load_domain_config(self):
        """載入領域特定配置"""
        domain_configs = {
            "satellite_communication": {
                "key_concepts": ["orbital_mechanics", "link_budget", "handover"],
                "essential_figures": ["system_model", "performance_comparison"],
                "technical_depth": "high"
            },
            "machine_learning": {
                "key_concepts": ["algorithm", "dataset", "evaluation"],
                "essential_figures": ["architecture", "results"],
                "technical_depth": "medium"
            }
        }
        
        self.config = domain_configs.get(self.domain, {})

    def customize_figure_importance(self, figure):
        """根據領域調整圖表重要性"""
        if self.domain == "satellite_communication":
            if "handover" in figure['description'].lower():
                figure['priority'] += 1
            if "performance" in figure['description'].lower():
                figure['teaching_value'] += 1
        
        return figure
```

---

## 📐 模板處理與版型設定

### 1. 模板載入與驗證
```python
def load_presentation_template(template_path="template.pptx"):
    """載入並驗證 PowerPoint 模板"""
    if os.path.exists(template_path):
        try:
            prs = Presentation(template_path)
            print(f"✅ 模板載入成功：{template_path}")
            print(f"   版型數量：{len(prs.slide_layouts)}")
            
            # 列出可用版型
            for i, layout in enumerate(prs.slide_layouts):
                print(f"   版型 {i}: {layout.name}")
            
            return prs
        except Exception as e:
            print(f"❌ 模板載入失敗：{e}")
            return Presentation()  # 使用預設模板
    else:
        print(f"⚠️  模板文件不存在，使用預設模板")
        return Presentation()
```

### 2. 版型索引對應
```python
# 常見版型索引 (依模板而異)
LAYOUT_INDICES = {
    'title': 0,           # 標題投影片
    'content': 1,         # 標題及內容
    'section': 2,         # 區段標題
    'two_content': 3,     # 兩項內容
    'comparison': 4,      # 比較
    'title_only': 5,      # 只有標題
    'blank': 6,           # 空白
    'content_caption': 7, # 內容及標題
    'picture_caption': 8, # 圖片及標題
}

def get_slide_layout(prs, layout_name):
    """安全取得投影片版型"""
    try:
        index = LAYOUT_INDICES.get(layout_name, 1)  # 預設使用內容版型
        return prs.slide_layouts[index]
    except IndexError:
        print(f"⚠️  版型索引 {index} 不存在，使用預設版型")
        return prs.slide_layouts[1]  # 備用方案
```

### 3. 投影片清理機制
```python
def clear_existing_slides(prs):
    """清理模板中的現有投影片，保留版型"""
    slide_count = len(prs.slides)
    for i in range(slide_count - 1, -1, -1):
        if i < len(prs.slides):
            rId = prs.slides._sldIdLst[i].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[i]
    
    print(f"✅ 已清理 {slide_count} 張現有投影片")
```

---

## 💻 完整程式碼範例

### 1. 基礎架構程式碼
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
import os
import re

def create_optimized_presentation():
    """創建最佳化 PowerPoint 簡報的完整範例"""
    
    # 1. 環境檢查
    print("🔍 檢查執行環境...")
    try:
        from pptx import Presentation
        print("✅ python-pptx 套件正常")
    except ImportError:
        print("❌ 請先安裝 python-pptx: pip install python-pptx")
        return
    
    # 2. 載入模板
    print("📂 載入簡報模板...")
    prs = load_presentation_template("template.pptx")
    
    # 3. 清理現有內容
    print("🧹 清理模板內容...")
    clear_existing_slides(prs)
    
    # 4. 定義內容限制
    MAX_LINES_PER_SLIDE = 20
    print(f"📏 每頁最大行數限制：{MAX_LINES_PER_SLIDE}")
    
    # 5. 創建投影片內容
    print("🎨 開始創建投影片...")
    
    # 標題頁
    slide1 = prs.slides.add_slide(prs.slide_layouts[0])
    slide1.shapes.title.text = "簡報標題"
    slide1.placeholders[1].text = "副標題內容"
    set_mixed_font_style(slide1.shapes.title.text_frame, font_size=22)
    set_mixed_font_style(slide1.placeholders[1].text_frame, font_size=16)
    
    # 內容頁面範例
    content_example = """• 重點項目一
• 重點項目二 Key Point Two
• 重點項目三 (含英文 English Content)
• 數據分析 Data Analysis: 25% improvement"""
    
    # 檢查內容長度並分頁
    content_parts = split_long_content(content_example, MAX_LINES_PER_SLIDE)
    create_multi_slide_content(prs, "內容標題", content_parts, prs.slide_layouts[1])
    
    # 6. 儲存簡報
    output_filename = "最佳化簡報範例.pptx"
    prs.save(output_filename)
    print(f"✅ 簡報創建完成：{output_filename}")
    print(f"📊 總投影片數：{len(prs.slides)}")
    
    return output_filename

# 執行範例
if __name__ == "__main__":
    create_optimized_presentation()
```

### 2. 執行腳本範例
```bash
#!/bin/bash
# 簡報製作自動化腳本

echo "🚀 開始 PowerPoint 簡報製作流程"

# 1. 啟用虛擬環境
echo "📦 啟用 Python 虛擬環境..."
source pptx_env/bin/activate

# 2. 驗證環境
echo "🔍 驗證 python-pptx 安裝..."
python -c "from pptx import Presentation; print('✅ 環境正常')" || {
    echo "❌ 環境異常，開始安裝套件..."
    pip install python-pptx
}

# 3. 執行簡報生成
echo "🎨 執行簡報生成腳本..."
python create_optimized_presentation.py

# 4. 驗證結果
if [ -f "最佳化簡報範例.pptx" ]; then
    echo "✅ 簡報生成成功"
    ls -la *.pptx
else
    echo "❌ 簡報生成失敗"
fi

echo "🏁 PowerPoint 簡報製作流程完成"
```

---

## 📋 最佳實務與注意事項

### 1. 智慧型簡報設計原則 (推薦)

#### 🤖 智慧型生成優勢
```markdown
🎯 **智慧型方法 - 最佳實務**
- 基於教學價值自動選擇最重要圖表
- 每個圖表配有深度技術解釋內容
- 自動確保教學邏輯完整性 (基礎→核心→驗證)
- 智慧內容分頁，避免投影片溢出
- 圖文精確對應，提升理解效果
- 自動品質檢查與優化建議
- 支援不同學術領域的定制化配置

📊 **圖表選擇策略**
- ⭐⭐⭐⭐⭐ 最高重要性：系統模型、核心演算法、實驗參數 (必選)
- ⭐⭐⭐⭐ 高重要性：性能比較、可靠性分析 (強烈建議)
- ⭐⭐⭐ 中等重要性：時域分析、容量分析 (可選)
- 🚫 避免選擇：裝飾性圖片、重複內容、次要細節
```

#### 📏 傳統設計原則 (手動製作參考)
```markdown
✅ **DO - 建議做法**
- 每頁內容控制在 15-20 行以內
- 標題使用 18-22pt 字體
- 內容使用 13-16pt 字體
- 程式碼使用 11-13pt 等寬字體
- 重要內容使用條列式組織
- 中英文混合時確保字體正確設定
- 長內容主動分頁，不要硬塞
- 優先使用原始論文圖表，提升專業度
- PDF 圖片提取後進行品質優化
- 圖片位置與相關內容保持對應

❌ **DON'T - 避免做法**
- 單頁內容超過 25 行
- 字體小於 11pt (觀眾難以閱讀)
- 中英文使用相同字體
- 忽略內容高度限制
- 過度使用小字體來塞入更多內容
- 複雜表格不考慮分頁顯示
- 忽略原始圖表，使用低品質截圖
- 圖片位置與內容不對應
- 提取的圖片不進行尺寸優化
- ❌ **最重要**: 隨意抓取所有圖片而不評估教學價值
```

### 2. 字體選擇建議
```python
# 字體優先順序設定
FONT_PREFERENCES = {
    'chinese': {
        'primary': '標楷體',      # Windows/Office 標準
        'fallback': ['DFKai-SB', 'BiauKai', 'SimSun', '微軟正黑體']
    },
    'english': {
        'primary': 'Times New Roman',  # 學術標準
        'fallback': ['Times', 'Liberation Serif', 'DejaVu Serif']
    },
    'code': {
        'primary': 'Consolas',     # 程式碼專用
        'fallback': ['Monaco', 'Courier New', 'monospace']
    }
}
```

### 3. 內容結構化建議
```python
# 投影片內容結構模板
SLIDE_STRUCTURE = {
    'title_slide': {
        'title': "主標題 (22pt, 標楷體+Times New Roman)",
        'subtitle': "副標題資訊 (16pt)",
        'max_lines': 8
    },
    'content_slide': {
        'title': "內容標題 (18pt)",
        'content': "條列式內容 (14-15pt)",
        'max_lines': 20
    },
    'code_slide': {
        'title': "程式碼標題 (18pt)",
        'content': "程式碼內容 (12pt, 等寬字體)",
        'max_lines': 25
    }
}
```

### 4. 效能最佳化
```python
def optimize_presentation_performance():
    """簡報效能最佳化建議"""
    tips = [
        "📊 使用 ASCII 表格而非嵌入物件",
        "🖼️  避免大量高解析度圖片",
        "📝 優先使用文字內容而非圖形",
        "🔄 重複使用相同版型減少檔案大小",
        "💾 定期儲存避免資料遺失",
        "🧹 清理未使用的投影片版型",
        "⚡ 分批處理大量投影片內容"
    ]
    return tips
```

---

## 🔧 故障排除指南

### 1. 常見錯誤與解決方案

#### **錯誤 1: AttributeError: 'int' object has no attribute 'pt'**
```python
# ❌ 錯誤寫法
content_height = Inches(6)
max_lines = int(content_height.pt / line_height)

# ✅ 正確寫法
content_height_pt = 6 * 72  # 直接使用 pt 單位
max_lines = int(content_height_pt / line_height)
```

#### **錯誤 2: 中英文字體設定失效**
```python
# ❌ 錯誤：整個段落統一字體
paragraph.font.name = "標楷體"

# ✅ 正確：逐字符設定字體
for run in paragraph.runs:
    if is_english_char(run.text):
        run.font.name = "Times New Roman"
    else:
        run.font.name = "標楷體"
```

#### **錯誤 3: 投影片內容溢出**
```python
# ❌ 錯誤：不檢查內容長度
slide.placeholders[1].text = very_long_content

# ✅ 正確：先檢查再分頁
content_parts = split_long_content(very_long_content, max_lines=20)
for part in content_parts:
    create_new_slide_with_content(part)
```

#### **錯誤 4: PDF 圖片提取失敗**
```python
# ❌ 錯誤：不檢查 PDF 文件狀態
pdf_document = fitz.open(pdf_path)  # 可能失敗

# ✅ 正確：加入錯誤處理
try:
    pdf_document = fitz.open(pdf_path)
    if pdf_document.is_closed:
        raise Exception("PDF 文件已關閉或損壞")
except Exception as e:
    print(f"❌ PDF 開啟失敗: {e}")
    return []
```

#### **錯誤 5: 圖片路徑不存在**
```python
# ❌ 錯誤：不檢查圖片文件存在
slide.shapes.add_picture(image_path, left, top, width, height)

# ✅ 正確：驗證文件存在性
if os.path.exists(image_path) and os.path.isfile(image_path):
    slide.shapes.add_picture(image_path, left, top, width, height)
else:
    print(f"❌ 圖片文件不存在: {image_path}")
```

### 2. 除錯檢查清單
```python
def debug_checklist():
    """簡報製作除錯檢查清單"""
    checklist = [
        "☑️  虛擬環境已正確啟用",
        "☑️  python-pptx 套件已安裝",
        "☑️  PDF 處理套件已安裝 (PyMuPDF, pdf2image)",
        "☑️  模板文件存在且可讀取",
        "☑️  PDF 文件可正常開啟",
        "☑️  圖片提取目錄已創建",
        "☑️  提取的圖片文件完整",
        "☑️  每頁內容行數 ≤ 20 行",
        "☑️  中英文字體正確分別設定",
        "☑️  字體大小適中 (≥ 12pt)",
        "☑️  長內容已適當分頁",
        "☑️  圖片與內容正確對應",
        "☑️  圖片尺寸已優化",
        "☑️  投影片可正常儲存",
        "☑️  生成的文件可正常開啟"
    ]
    return checklist
```

### 3. 測試驗證腳本
```python
def validate_presentation(pptx_file):
    """驗證生成的簡報文件"""
    try:
        # 嘗試載入文件
        prs = Presentation(pptx_file)
        print(f"✅ 文件載入成功: {pptx_file}")
        
        # 檢查投影片數量
        slide_count = len(prs.slides)
        print(f"📊 投影片數量: {slide_count}")
        
        # 檢查每張投影片
        for i, slide in enumerate(prs.slides):
            if slide.shapes.title:
                title_text = slide.shapes.title.text
                print(f"   投影片 {i+1}: {title_text[:30]}...")
        
        return True
    except Exception as e:
        print(f"❌ 文件驗證失敗: {e}")
        return False
```

---

## 📚 參考資源

### 1. 技術文件
- **python-pptx 官方文檔**: https://python-pptx.readthedocs.io/
- **PowerPoint 物件模型**: Microsoft Office 開發者文檔
- **字體相容性指南**: 跨平台字體選擇建議

### 2. 相關工具
```bash
# 字體檢測工具
fc-list | grep -i "標楷體"
fc-list | grep -i "times"

# PowerPoint 文件檢測
file *.pptx
unzip -l *.pptx  # 檢查內部結構
```

### 3. 版本相容性
```python
# 支援的 Python 版本
PYTHON_VERSIONS = ["3.7+", "3.8+", "3.9+", "3.10+", "3.11+"]

# 支援的 PowerPoint 版本
POWERPOINT_VERSIONS = ["2013", "2016", "2019", "2021", "365"]

# 支援的作業系統
SUPPORTED_OS = ["Windows 10+", "macOS 10.14+", "Ubuntu 18.04+"]
```

---

## 🚀 快速上手指南

### 🎯 智慧型生成 (推薦)
```bash
# 1. 進入工具目錄
cd /home/sat/ntn-stack/tools/powerpoint_generators

# 2. 執行智慧型簡報生成
python create_intelligent_pptx.py

# 3. 檢查輸出結果
ls -la ../../doc/LEO衛星MC-HO演算法智慧簡報.pptx
cat ../../doc/智慧簡報創建報告.md
```

### 📊 效果對比

| 特性 | 傳統方法 | 智慧型方法 |
|------|----------|------------|
| 圖表選擇 | 手動隨意選擇 | **基於教學價值自動篩選** |
| 內容深度 | 只有圖片，無說明 | **每圖表配有詳細技術解釋** |
| 教學邏輯 | 無結構規劃 | **完整教學流程 (基礎→核心→驗證)** |
| 品質控制 | 手動檢查 | **自動品質驗證與優化建議** |
| 時間成本 | 數小時手動調整 | **幾分鐘自動生成** |
| 專業程度 | 依製作者經驗 | **基於學術標準的一致品質** |

### 💡 使用建議

#### 🎓 學術場合
- **論文答辯**: 使用智慧型生成，確保技術完整性
- **課程教學**: 調整 `max_figures=3-5` 控制內容量
- **會議報告**: 重點選擇 `teaching_focus="performance"`

#### 🏢 企業應用
- **技術分享**: 使用領域特定生成器
- **培訓教材**: 增加實用案例說明
- **產品展示**: 突出量化效益數據

---

## 📞 技術支援

### 🆕 智慧型工具支援
- **智慧圖表選擇器**: `intelligent_figure_selector.py`
- **智慧型簡報生成器**: `create_intelligent_pptx.py`  
- **完整使用指南**: `README.md`

### 聯絡資訊
- **問題回報**: GitHub Issues 或專案維護者
- **技術討論**: 開發團隊內部群組
- **文檔更新**: 請提交 Pull Request

### 版本記錄
- **v3.0** (2024-09-06): 智慧型圖表選擇與生成系統
- **v2.1** (2024-09): PDF 圖片提取技術整合
- **v2.0** (2024-09): 中英文字體混合與高度控制
- **v1.0** (2024-08): 基礎 PowerPoint 生成功能
- **v1.0**: 基礎簡報生成功能
- **v1.1**: 新增中英文字體混合支援
- **v1.2**: 實作投影片高度自動控制
- **v1.3**: 完善內容分頁機制 (當前版本)

---

*本指南基於 LEO 衛星 MC-HO 演算法簡報專案的最佳實務經驗整理，適用於所有基於 python-pptx 的 PowerPoint 簡報開發專案。*