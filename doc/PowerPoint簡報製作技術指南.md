# PowerPoint 簡報製作技術指南
## 基於 python-pptx 的專業簡報開發流程

---

## 📋 目錄
1. [環境準備與套件安裝](#環境準備與套件安裝)
2. [投影片高度控制技術](#投影片高度控制技術)
3. [中英文字體混合設定](#中英文字體混合設定)
4. [內容分頁機制](#內容分頁機制)
5. [PDF 圖片與表格提取技術](#pdf-圖片與表格提取技術)
6. [模板處理與版型設定](#模板處理與版型設定)
7. [完整程式碼範例](#完整程式碼範例)
8. [最佳實務與注意事項](#最佳實務與注意事項)
9. [故障排除指南](#故障排除指南)

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

### 1. 內容設計原則
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

## 📞 技術支援

### 聯絡資訊
- **問題回報**: GitHub Issues 或專案維護者
- **技術討論**: 開發團隊內部群組
- **文檔更新**: 請提交 Pull Request

### 版本記錄
- **v1.0**: 基礎簡報生成功能
- **v1.1**: 新增中英文字體混合支援
- **v1.2**: 實作投影片高度自動控制
- **v1.3**: 完善內容分頁機制 (當前版本)

---

*本指南基於 LEO 衛星 MC-HO 演算法簡報專案的最佳實務經驗整理，適用於所有基於 python-pptx 的 PowerPoint 簡報開發專案。*