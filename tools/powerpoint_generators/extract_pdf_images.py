#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import fitz  # PyMuPDF
from pdf2image import convert_from_path
from PIL import Image
import os
import json

def extract_images_from_pdf(pdf_path, output_dir="extracted_images"):
    """從 PDF 中提取所有圖片"""
    
    # 創建輸出目錄
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 打開 PDF 文件
    pdf_document = fitz.open(pdf_path)
    extracted_info = []
    
    print(f"🔍 開始分析 PDF：{pdf_path}")
    print(f"📄 總頁數：{len(pdf_document)}")
    
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        print(f"\n📃 處理第 {page_num + 1} 頁...")
        
        # 提取頁面中的圖片
        image_list = page.get_images(full=True)
        
        if image_list:
            print(f"   發現 {len(image_list)} 個圖片物件")
            
            for img_index, img in enumerate(image_list):
                try:
                    # 獲取圖片資料
                    xref = img[0]
                    pix = fitz.Pixmap(pdf_document, xref)
                    
                    # 跳過太小的圖片（可能是裝飾性元素）
                    if pix.width < 100 or pix.height < 100:
                        print(f"   ⏭️  跳過小圖片 ({pix.width}x{pix.height})")
                        pix = None
                        continue
                    
                    # 儲存圖片
                    if pix.n - pix.alpha < 4:  # 檢查顏色空間
                        img_filename = f"page_{page_num+1}_img_{img_index+1}.png"
                        img_path = os.path.join(output_dir, img_filename)
                        pix.save(img_path)
                        
                        print(f"   ✅ 提取圖片：{img_filename} ({pix.width}x{pix.height})")
                        
                        # 記錄圖片資訊
                        extracted_info.append({
                            "page": page_num + 1,
                            "image_index": img_index + 1,
                            "filename": img_filename,
                            "width": pix.width,
                            "height": pix.height,
                            "path": img_path
                        })
                    else:
                        print(f"   ⚠️  跳過 CMYK 圖片")
                    
                    pix = None
                    
                except Exception as e:
                    print(f"   ❌ 提取圖片失敗：{e}")
        else:
            print("   📭 此頁面沒有發現圖片")
    
    pdf_document.close()
    
    # 保存提取資訊
    info_file = os.path.join(output_dir, "extraction_info.json")
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_info, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 提取完成！")
    print(f"   總共提取：{len(extracted_info)} 個圖片")
    print(f"   輸出目錄：{output_dir}")
    
    return extracted_info

def extract_high_res_pages(pdf_path, output_dir="page_images", specific_pages=None):
    """提取特定頁面為高解析度圖片"""
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"🖼️  轉換頁面為高解析度圖片...")
    
    # 指定要提取的頁面（論文中重要圖表的頁面）
    if specific_pages is None:
        # 根據論文內容，這些頁面包含重要圖表
        specific_pages = [1, 2, 3, 4, 5, 6]  # Figure 1, 2, 3, 4, 5, 6 等
    
    try:
        # 轉換特定頁面
        images = convert_from_path(
            pdf_path, 
            dpi=300,  # 高解析度
            first_page=min(specific_pages) if specific_pages else 1,
            last_page=max(specific_pages) if specific_pages else 6
        )
        
        extracted_pages = []
        for i, (image, page_num) in enumerate(zip(images, specific_pages)):
            page_filename = f"page_{page_num}_high_res.png"
            page_path = os.path.join(output_dir, page_filename)
            image.save(page_path, 'PNG', quality=95)
            
            print(f"   ✅ 頁面 {page_num}：{page_filename}")
            
            extracted_pages.append({
                "page": page_num,
                "filename": page_filename,
                "width": image.width,
                "height": image.height,
                "path": page_path
            })
        
        return extracted_pages
    
    except Exception as e:
        print(f"   ❌ 頁面提取失敗：{e}")
        return []

def identify_figures_and_tables(pdf_path):
    """識別論文中的圖表位置和標題"""
    
    pdf_document = fitz.open(pdf_path)
    figures_tables = []
    
    print(f"🔍 搜尋論文中的圖表...")
    
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text = page.get_text()
        
        # 搜尋 Figure 關鍵字
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            if 'Fig.' in line or 'Figure' in line or 'TABLE' in line or 'Table' in line:
                # 找到可能的圖表標題
                clean_line = line.strip()
                if clean_line:
                    figures_tables.append({
                        "page": page_num + 1,
                        "line": line_num,
                        "text": clean_line,
                        "type": "Figure" if "Fig" in clean_line else "Table"
                    })
                    print(f"   📊 頁面 {page_num + 1}: {clean_line}")
    
    pdf_document.close()
    
    print(f"📋 找到 {len(figures_tables)} 個圖表引用")
    return figures_tables

def main():
    """主要執行函數"""
    
    pdf_file = "2024_10_Enhancing_Handover_Performance_in_LEO_Satellite_Networks_with_Multi-Connectivity_and_Conditional_Handover_Approach.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ 找不到 PDF 文件：{pdf_file}")
        return
    
    print("🚀 開始 PDF 圖表提取流程")
    print("=" * 60)
    
    # 1. 識別圖表位置
    figures_info = identify_figures_and_tables(pdf_file)
    
    print("\n" + "=" * 60)
    
    # 2. 提取嵌入的圖片
    extracted_images = extract_images_from_pdf(pdf_file, "論文圖片")
    
    print("\n" + "=" * 60)
    
    # 3. 提取重要頁面的高解析度圖片
    page_images = extract_high_res_pages(pdf_file, "論文頁面", [1, 2, 3, 4, 5, 6])
    
    print("\n" + "=" * 60)
    print("📋 提取摘要：")
    print(f"   圖表引用：{len(figures_info)} 個")
    print(f"   提取圖片：{len(extracted_images)} 個")
    print(f"   頁面圖片：{len(page_images)} 個")
    
    # 保存完整摘要
    summary = {
        "pdf_file": pdf_file,
        "figures_and_tables": figures_info,
        "extracted_images": extracted_images,
        "page_images": page_images,
        "timestamp": "2024-09-06"
    }
    
    with open("pdf_extraction_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print("✅ PDF 圖表提取完成！")

if __name__ == "__main__":
    main()