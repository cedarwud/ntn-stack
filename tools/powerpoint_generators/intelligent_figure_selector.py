#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧圖表選擇器 - 基於教學價值和重要性評估
Intelligent Figure Selector for PowerPoint Generation
"""

import json
import os
from typing import Dict, List, Tuple

class IntelligentFigureSelector:
    """智慧圖表選擇器，根據教學價值和論文重要性選擇最佳圖表組合"""
    
    def __init__(self):
        self.figure_importance = {
            # 最高重要性 - 基礎概念與核心演算法
            "Figure 1": {
                "priority": 1,
                "teaching_value": 5,
                "technical_importance": 5,
                "description": "LEO 衛星覆蓋場景圖 - 系統模型基礎",
                "key_concepts": [
                    "Multi-coverage 重疊區域概念",
                    "衛星運動與覆蓋範圍變化", 
                    "LEO 衛星星座架構",
                    "用戶設備 (UE) 分布模型"
                ],
                "teaching_focus": "建立 LEO 衛星網路的基本概念，理解多重覆蓋區域如何形成"
            },
            
            "Figure 2": {
                "priority": 1,
                "teaching_value": 5,
                "technical_importance": 5,
                "description": "MC-HO 演算法流程圖 - 核心技術貢獻",
                "key_concepts": [
                    "Master Node (MN) 與 Secondary Node (SN) 架構",
                    "Packet Duplication 機制",
                    "條件式切換 (CHO) 觸發條件",
                    "Path-switching 程序",
                    "Location-based 觸發準則"
                ],
                "teaching_focus": "深入理解 MC-HO 演算法的完整執行流程與技術細節"
            },
            
            "Table 1": {
                "priority": 1,
                "teaching_value": 4,
                "technical_importance": 4,
                "description": "模擬參數表 - 實驗設置完整參數",
                "key_concepts": [
                    "LEO 衛星軌道高度 (600km)",
                    "衛星運行速度 (7.56km/s)",
                    "S-Band 頻率設定 (2GHz)",
                    "3GPP NTN 標準參數",
                    "Dense Urban 場景配置"
                ],
                "teaching_focus": "了解 LEO 衛星系統的實際工程參數與模擬環境設定"
            },
            
            # 高重要性 - 性能驗證與比較
            "Figure 3": {
                "priority": 2,
                "teaching_value": 4,
                "technical_importance": 4,
                "description": "平均換手次數比較 - 核心性能指標",
                "key_concepts": [
                    "SC-HO vs MC-HO 性能比較",
                    "Beam Overlap 影響分析",
                    "換手次數顯著減少 (40%重疊: 247→130 HOs/s)",
                    "Location-based 觸發機制效益"
                ],
                "teaching_focus": "量化展示 MC-HO 相對於傳統 SC-HO 的性能優勢"
            },
            
            "Figure 4": {
                "priority": 2,
                "teaching_value": 4,
                "technical_importance": 4,
                "description": "無線連結失效 (RLF) 分析 - 系統可靠性",
                "key_concepts": [
                    "Radio Link Failure 定義與測量",
                    "Packet Duplication 提升連結穩定性",
                    "Transmit Diversity 實際效益",
                    "干擾環境下的性能表現",
                    "Selection Combining 機制"
                ],
                "teaching_focus": "理解 MC-HO 如何透過雙連線架構提升系統可靠性"
            },
            
            # 中等重要性 - 深度分析
            "Figure 5": {
                "priority": 3,
                "teaching_value": 3,
                "technical_importance": 3,
                "description": "時間序列換手分析 - 動態行為研究",
                "key_concepts": [
                    "LEO 衛星快速移動特性 (7秒覆蓋周期)",
                    "時域性能穩定性分析",
                    "Peak 換手負載分析",
                    "系統長期運行行為"
                ],
                "teaching_focus": "分析 LEO 衛星高速移動環境下的系統動態特性"
            },
            
            "Figure 6": {
                "priority": 3,
                "teaching_value": 3,
                "technical_importance": 3,
                "description": "系統容量分析 - 頻譜效率權衡",
                "key_concepts": [
                    "Beam Overlap 對容量影響",
                    "干擾與頻譜效率權衡",
                    "MC-HO 容量保持能力",
                    "Distance Offset 參數影響",
                    "SINR 改善效果"
                ],
                "teaching_focus": "理解多重連線架構下的容量與干擾權衡考量"
            }
        }
        
        # 定義圖表映射關係 (論文圖表 -> 提取的圖片檔案)
        self.figure_image_mapping = {
            "Figure 1": "page_2_img_1.png",
            "Figure 2": None,  # 流程圖可能需要重新繪製
            "Table 1": "page_4_img_3.png",  # 參數表
            "Figure 3": "page_4_img_1.png", # 換手次數比較
            "Figure 4": "page_4_img_2.png", # RLF分析  
            "Figure 5": "page_5_img_1.png", # 時間序列
            "Figure 6": "page_5_img_2.png"  # 容量分析
        }

    def select_figures_by_priority(self, max_figures: int = 5) -> List[Dict]:
        """根據優先級和教學價值選擇最重要的圖表"""
        
        # 按優先級和教學價值排序
        sorted_figures = sorted(
            self.figure_importance.items(),
            key=lambda x: (x[1]['priority'], -x[1]['teaching_value'])
        )
        
        selected_figures = []
        for figure_name, figure_info in sorted_figures[:max_figures]:
            image_file = self.figure_image_mapping.get(figure_name)
            
            selected_figures.append({
                "figure_name": figure_name,
                "image_file": image_file,
                "priority": figure_info['priority'],
                "teaching_value": figure_info['teaching_value'],
                "description": figure_info['description'],
                "key_concepts": figure_info['key_concepts'],
                "teaching_focus": figure_info['teaching_focus'],
                "slide_title": f"{figure_name}: {figure_info['description']}"
            })
        
        return selected_figures

    def generate_figure_explanations(self, selected_figures: List[Dict]) -> Dict[str, str]:
        """為選中的圖表生成詳細的教學說明內容"""
        
        explanations = {}
        
        for figure in selected_figures:
            figure_name = figure['figure_name']
            
            if figure_name == "Figure 1":
                explanations[figure_name] = self._generate_figure1_explanation()
            elif figure_name == "Figure 2":
                explanations[figure_name] = self._generate_figure2_explanation()
            elif figure_name == "Table 1":
                explanations[figure_name] = self._generate_table1_explanation()
            elif figure_name == "Figure 3":
                explanations[figure_name] = self._generate_figure3_explanation()
            elif figure_name == "Figure 4":
                explanations[figure_name] = self._generate_figure4_explanation()
            elif figure_name == "Figure 5":
                explanations[figure_name] = self._generate_figure5_explanation()
            elif figure_name == "Figure 6":
                explanations[figure_name] = self._generate_figure6_explanation()
        
        return explanations

    def _generate_figure1_explanation(self) -> str:
        return """LEO 衛星系統覆蓋模型與基礎架構

🛰️ 系統架構特點：
• LEO 衛星軌道高度：600km（低於 GEO 的 35,786km）
• 衛星運行速度：7.56km/s（高速移動特性）
• 波束直徑：50km（相對較小的覆蓋範圍）
• 多衛星覆蓋重疊設計：減少覆蓋空隙

📡 多重覆蓋區域 (Multi-coverage Area)：
• 相鄰衛星波束重疊區域
• 用戶設備可同時連接多顆衛星
• MC-HO 演算法的核心應用場景
• 提供 Soft Handover 的技術基礎

🌐 與 GEO/MEO 的差異：
• 低延遲：~2.5ms vs GEO 的 ~250ms
• 高動態性：需要頻繁的切換管理
• 更好的功率預算：距離較近，訊號強度佳"""

    def _generate_figure2_explanation(self) -> str:
        return """MC-HO 演算法完整執行流程

🔄 四階段執行流程：

1️⃣ 初始化階段：
• UE 連接到服務衛星 (SSAT) 作為 Master Node (MN)
• 基於 GNSS 與星曆資料確定位置
• 監測與候選衛星 (TSAT) 的距離

2️⃣ 條件觸發階段：
• Location-based CHO 條件檢查：
  dTSAT(t) ≤ Rb - doffset && dSSAT(t) ≤ Rb - doffset
• 進入多重覆蓋區域時啟動 MC 架構
• 開始與 TSAT 的 Random Access 程序

3️⃣ 雙連線階段：
• TSAT 加入為 Secondary Node (SN)
• 啟動 Packet Duplication 機制
• UE 同時接收來自 MN 和 SN 的數據
• Selection Combining：選擇最佳 SINR 連結

4️⃣ 路徑切換階段：
• TSAT 成為新的 MN
• 透過 AMF 執行 Bearer Modification
• 釋放與原 SSAT 的連接
• 準備下一次切換循環"""

    def _generate_table1_explanation(self) -> str:
        return """LEO 衛星系統模擬參數與 3GPP NTN 標準

🛰️ 軌道與物理參數：
• 地球半徑：6371 km（標準值）
• LEO 衛星高度：600 km（典型 LEO 高度範圍）
• 衛星發射功率：30 dBi 最大增益
• 等效全向輻射功率：34 dBW/MHz

📡 通訊系統參數：
• 載波頻率：2 GHz (S-Band)
• 系統頻寬：30 MHz
• 雜訊功率：-121.4 dBm
• 用戶密度：1 user/km²（Dense Urban）

🎯 切換參數設定：
• Distance Offset：1km / 5km
• 衛星移動速度：7.56 km/s（軌道速度）
• 模擬時間：200 秒
• 時間間隔：0.5 秒

📋 3GPP NTN 合規性：
• 路徑損耗模型：遵循 3GPP TR 38.811 Dense Urban
• Shadow Fading：基於仰角動態調整
• 干擾模型：考慮相鄰衛星同頻干擾"""

    def _generate_figure3_explanation(self) -> str:
        return """換手次數性能比較：MC-HO vs SC-HO

📊 關鍵性能數據：
• 0% 重疊：兩種方法性能相同（148 HOs/s）
• 10% 重疊：SC-HO 165 vs MC-HO 162 HOs/s
• 20% 重疊：SC-HO 185 vs MC-HO 145 HOs/s
• 30% 重疊：SC-HO 212 vs MC-HO 129 HOs/s  
• 40% 重疊：SC-HO 247 vs MC-HO 130 HOs/s

🎯 MC-HO 優勢分析：
• 高重疊區域效益顯著：40% 時減少 47% 換手次數
• 雙連線架構提供穩定過渡期
• Location-based CHO 減少不必要的切換
• Soft Handover 特性避免頻繁硬切換

⚡ 技術原理：
• Packet Duplication 延長服務衛星連接時間
• Selection Combining 提供更穩定的服務品質
• 多重覆蓋區域充分利用，減少邊緣效應
• 條件式切換避免 Ping-pong 現象"""

    def _generate_figure4_explanation(self) -> str:
        return """無線連結失效 (RLF) 可靠性分析

📡 RLF 定義與測量：
• 服務衛星 SINR < -8 dB 持續 0.5 秒
• 代表連結品質嚴重劣化，無法維持通訊
• LEO 環境下的關鍵可靠性指標

🔄 MC-HO 可靠性機制：
• Transmit Diversity：同時接收兩個衛星訊號
• Selection Combining：動態選擇最佳 SINR 連結
• Packet Duplication：重要數據雙重傳輸
• 冗余連接：一個連結失效時另一個維持服務

📈 性能改善數據：
• 20% 重疊：SC-HO 296 vs MC-HO 265 failures/s
• 30% 重疊：SC-HO 403 vs MC-HO 338 failures/s
• 40% 重疊：SC-HO 532 vs MC-HO 410 failures/s
• 高重疊環境下 RLF 減少約 23%

🌐 實際應用效益：
• 減少通話中斷和數據傳輸錯誤
• 提升用戶體驗品質 (QoE)
• 降低重傳開銷和網路負載
• 增強系統整體穩定性"""

    def _generate_figure5_explanation(self) -> str:
        return """LEO 衛星時間域動態行為分析

⏱️ 時域特性觀察：
• 模擬時長：100 秒觀察期
• SC-HO 換手範圍：150-325 次
• MC-HO 換手範圍：100-159 次（更穩定）
• 每 7 秒出現換手峰值（衛星覆蓋周期）

🛰️ LEO 衛星高速移動特性：
• 軌道速度：7.56 km/s
• 波束直徑：50 km
• 覆蓋時間：約 6.6 秒 (50km ÷ 7.56km/s)
• 需要頻繁且快速的切換決策

📊 MC-HO 穩定性優勢：
• 換手峰值明顯較低且平滑
• 減少突發性大量切換需求
• 提供更一致的網路性能
• 降低核心網路信令負載

🎯 實際應用意義：
• 更好的服務連續性保證
• 減少因頻繁切換造成的服務中斷
• 適合高品質即時應用 (VoIP, 視訊通話)
• 提升整體網路穩定度"""

    def _generate_figure6_explanation(self) -> str:
        return """系統容量與頻譜效率權衡分析

📶 容量趨勢分析：
• 重疊增加 → 容量下降（符合理論預期）
• MC-HO 始終保持優於 SC-HO 的容量性能
• Distance Offset (1km vs 5km) 對容量影響有限
• Transmit Diversity 補償干擾損失

🔬 技術原理解釋：
• 重疊區域增加 → 同頻干擾增強
• MC-HO 透過 Selection Combining 改善 SINR
• 雙連線提供更好的訊號品質選擇
• 減少邊緣用戶的性能劣化

⚖️ 系統設計權衡：
• 重疊 vs 干擾：需找到最佳平衡點
• 容量 vs 可靠性：MC-HO 提供更好的綜合性能
• 複雜度 vs 效益：雙連線架構的合理性
• 頻譜效率 vs 服務品質的平衡考量

🎯 工程實務建議：
• 20-30% 重疊為較佳設計點
• MC-HO 在所有重疊條件下都有優勢
• 適合對可靠性要求高的應用場景
• 可透過智慧排程進一步優化性能"""

    def generate_selection_report(self, selected_figures: List[Dict]) -> str:
        """生成圖表選擇報告"""
        
        report = "# 📊 智慧圖表選擇報告\n\n"
        report += "## 🎯 選擇策略\n"
        report += "基於教學價值與技術重要性的綜合評估，優先選擇最具教學效果的圖表。\n\n"
        
        report += "## 📋 選中圖表清單\n\n"
        for i, figure in enumerate(selected_figures, 1):
            report += f"### {i}. {figure['figure_name']}\n"
            report += f"**描述**: {figure['description']}\n"
            report += f"**優先級**: {figure['priority']} | **教學價值**: {'⭐' * figure['teaching_value']}\n"
            report += f"**圖片檔案**: {figure['image_file'] or '需要重新製作'}\n"
            report += f"**教學焦點**: {figure['teaching_focus']}\n\n"
        
        total_priority_1 = sum(1 for fig in selected_figures if fig['priority'] == 1)
        total_priority_2 = sum(1 for fig in selected_figures if fig['priority'] == 2)
        
        report += "## 📈 選擇統計\n"
        report += f"- 最高重要性圖表: {total_priority_1} 個\n"
        report += f"- 高重要性圖表: {total_priority_2} 個\n"
        report += f"- 總計: {len(selected_figures)} 個圖表\n\n"
        
        report += "## ✅ 教學完整性檢查\n"
        report += "- ✅ 基礎概念建立 (Figure 1)\n"
        report += "- ✅ 核心演算法說明 (Figure 2)\n"  
        report += "- ✅ 實驗參數展示 (Table 1)\n"
        report += "- ✅ 性能驗證對比 (Figure 3, 4)\n"
        
        return report

def main():
    """主程式：執行智慧圖表選擇"""
    
    selector = IntelligentFigureSelector()
    
    # 選擇最重要的 5 個圖表
    selected_figures = selector.select_figures_by_priority(max_figures=5)
    
    # 生成詳細說明
    explanations = selector.generate_figure_explanations(selected_figures)
    
    # 生成選擇報告  
    report = selector.generate_selection_report(selected_figures)
    
    # 輸出結果
    print("🎯 智慧圖表選擇完成！")
    print(f"✅ 選中 {len(selected_figures)} 個最重要的圖表")
    print("\n" + "="*60)
    print(report)
    
    # 儲存選擇結果
    results = {
        "selected_figures": selected_figures,
        "explanations": explanations,
        "selection_report": report,
        "timestamp": "2024-09-06"
    }
    
    with open('intelligent_figure_selection.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("💾 結果已儲存至 intelligent_figure_selection.json")

if __name__ == "__main__":
    main()