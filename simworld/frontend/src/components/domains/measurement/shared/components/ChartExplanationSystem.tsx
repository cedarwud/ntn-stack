/**
 * 圖表說明系統
 * 
 * 完成 Phase 3.2 要求：
 * - 統一的圖表說明界面
 * - 互動式說明和提示
 * - 多層次說明內容 (基礎/標準/專家)
 * - 上下文相關的幫助系統
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui'
import {
  HelpCircle,
  Info,
  BookOpen,
  ChevronDown,
  ChevronRight,
  Lightbulb,
  Target,
  Zap,
  Eye,
  X
} from 'lucide-react'

interface ChartExplanationProps {
  chartType: 'A4' | 'D1' | 'D2' | 'T1' | 'SIB19'
  isVisible: boolean
  onClose: () => void
  viewMode?: 'simple' | 'standard' | 'expert'
  className?: string
}

interface ExplanationContent {
  title: string
  description: string
  keyPoints: string[]
  technicalDetails?: string[]
  examples?: string[]
  relatedConcepts?: string[]
}

const CHART_EXPLANATIONS: Record<string, ExplanationContent> = {
  A4: {
    title: 'A4 事件 - 位置補償測量',
    description: 'A4 事件用於測量和補償 UE 位置誤差，確保定位精度滿足服務要求。',
    keyPoints: [
      '監控 UE 與參考位置的距離差異',
      '當距離差超過門檻值時觸發位置補償',
      '補償範圍限制在 ±3km 以內',
      '使用多顆衛星進行精確定位'
    ],
    technicalDetails: [
      '基於 3GPP TS 38.331 標準實現',
      '使用 SIB19 統一平台提供的衛星星曆',
      '支援仰角 (50%) + 距離 (30%) + 軌道穩定性 (20%) 的衛星選擇算法',
      '位置補償精度可達亞米級'
    ],
    examples: [
      '城市峽谷環境下的定位補償',
      '高速移動場景的位置追蹤',
      '室內外切換的位置連續性'
    ],
    relatedConcepts: [
      'GNSS 定位原理',
      '多路徑效應',
      '衛星幾何稀釋精度 (GDOP)',
      'RTK 差分定位'
    ]
  },
  D1: {
    title: 'D1 事件 - 雙重距離測量',
    description: 'D1 事件監控 UE 與參考位置的距離變化，支援全球任意參考位置設定。',
    keyPoints: [
      '同時監控兩個距離門檻值',
      '支援全球化地理座標設定',
      '提供距離變化趨勢分析',
      '可配置遲滯值防止頻繁觸發'
    ],
    technicalDetails: [
      '使用大圓距離計算公式',
      '考慮地球橢球體模型 (WGS84)',
      '支援海拔高度差異計算',
      '距離精度可達米級'
    ],
    examples: [
      '跨國漫遊的距離監控',
      '邊界區域的位置管理',
      '大範圍移動的軌跡追蹤'
    ],
    relatedConcepts: [
      '大圓距離計算',
      'WGS84 座標系統',
      '地理資訊系統 (GIS)',
      '位置區域管理'
    ]
  },
  D2: {
    title: 'D2 事件 - 動態參考位置',
    description: 'D2 事件追蹤移動參考位置 (如衛星)，監控相對距離變化。',
    keyPoints: [
      '追蹤 LEO 衛星的真實軌道 (90分鐘週期)',
      '計算衛星距離和地面投影距離',
      '提供軌道軌跡預測',
      '監控星曆有效期並提醒更新'
    ],
    technicalDetails: [
      '基於 SGP4 軌道模型計算',
      '軌道高度 550km，傾角 53度',
      '衛星速度約 27,000 km/h',
      '軌道預測精度 < 1km'
    ],
    examples: [
      'Starlink 衛星追蹤',
      'OneWeb 網路優化',
      '衛星切換預測'
    ],
    relatedConcepts: [
      'SGP4 軌道模型',
      'TLE 軌道根數',
      'LEO 衛星星座',
      '軌道力學'
    ]
  },
  T1: {
    title: 'T1 事件 - 時間同步監控',
    description: 'T1 事件監控 GNSS 時間同步狀態，確保時間精度滿足系統要求。',
    keyPoints: [
      '監控 GNSS 時間同步精度 (< 10ms)',
      '檢測時鐘偏移量 (± 50ms)',
      '提供時間窗口管理',
      '支援同步失敗的警告和恢復'
    ],
    technicalDetails: [
      '基於 GPS/Galileo/BeiDou 多系統',
      '時間精度可達納秒級',
      '支援 UTC 和 GNSS 時間轉換',
      '提供時間同步品質指標'
    ],
    examples: [
      '5G 網路時間同步',
      '金融交易時間戳',
      '科學實驗時間基準'
    ],
    relatedConcepts: [
      'GNSS 時間系統',
      'UTC 協調世界時',
      '時間同步協議',
      '原子鐘技術'
    ]
  },
  SIB19: {
    title: 'SIB19 統一平台',
    description: 'SIB19 提供統一的衛星資訊廣播，為所有測量事件提供一致的數據基礎。',
    keyPoints: [
      '統一的衛星星曆和時間基準',
      '支援所有測量事件的數據需求',
      '提供事件特定的數據萃取',
      '確保跨事件的數據一致性'
    ],
    technicalDetails: [
      '符合 3GPP TS 38.331 標準',
      '支援 NTN (非地面網路) 規範',
      '提供 11 個標準化數據字段',
      '更新週期可配置 (1-24小時)'
    ],
    examples: [
      '多事件協調測量',
      '系統級性能優化',
      '標準化數據交換'
    ],
    relatedConcepts: [
      '3GPP NTN 標準',
      '系統資訊廣播',
      '衛星通信協議',
      '網路資源管理'
    ]
  }
}

export const ChartExplanationSystem: React.FC<ChartExplanationProps> = ({
  chartType,
  isVisible,
  onClose,
  viewMode = 'standard',
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState('overview')
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['keyPoints']))

  const explanation = CHART_EXPLANATIONS[chartType]

  const toggleSection = useCallback((sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId)
      } else {
        newSet.add(sectionId)
      }
      return newSet
    })
  }, [])

  // 根據視圖模式過濾內容
  const getFilteredContent = useCallback(() => {
    switch (viewMode) {
      case 'simple':
        return {
          showTechnicalDetails: false,
          showExamples: true,
          showRelatedConcepts: false
        }
      case 'standard':
        return {
          showTechnicalDetails: true,
          showExamples: true,
          showRelatedConcepts: false
        }
      case 'expert':
        return {
          showTechnicalDetails: true,
          showExamples: true,
          showRelatedConcepts: true
        }
      default:
        return {
          showTechnicalDetails: true,
          showExamples: true,
          showRelatedConcepts: false
        }
    }
  }, [viewMode])

  const contentFilter = getFilteredContent()

  if (!isVisible || !explanation) {
    return null
  }

  // 渲染可摺疊區塊
  const renderCollapsibleSection = (
    id: string,
    title: string,
    icon: React.ReactNode,
    content: string[] | undefined,
    badge?: string
  ) => {
    if (!content || content.length === 0) return null

    const isExpanded = expandedSections.has(id)

    return (
      <Collapsible>
        <CollapsibleTrigger
          onClick={() => toggleSection(id)}
          className="flex items-center justify-between w-full p-3 hover:bg-muted rounded-lg transition-colors"
        >
          <div className="flex items-center gap-2">
            {icon}
            <span className="font-medium">{title}</span>
            {badge && <Badge variant="outline" className="text-xs">{badge}</Badge>}
          </div>
          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </CollapsibleTrigger>
        
        <CollapsibleContent className="px-3 pb-3">
          <ul className="space-y-2 mt-2">
            {content.map((item, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </CollapsibleContent>
      </Collapsible>
    )
  }

  return (
    <div className={`chart-explanation-system ${className}`}>
      <Card className="w-full max-w-4xl">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              {explanation.title}
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{viewMode} 模式</Badge>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">概覽</TabsTrigger>
              <TabsTrigger value="details">詳細說明</TabsTrigger>
              <TabsTrigger value="interactive">互動指南</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="mt-4">
              <div className="space-y-4">
                {/* 基本描述 */}
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm leading-relaxed">{explanation.description}</p>
                </div>

                {/* 關鍵要點 */}
                {renderCollapsibleSection(
                  'keyPoints',
                  '關鍵要點',
                  <Target className="h-4 w-4" />,
                  explanation.keyPoints,
                  `${explanation.keyPoints.length} 項`
                )}

                {/* 應用示例 */}
                {contentFilter.showExamples && renderCollapsibleSection(
                  'examples',
                  '應用示例',
                  <Lightbulb className="h-4 w-4" />,
                  explanation.examples,
                  '實際案例'
                )}
              </div>
            </TabsContent>

            <TabsContent value="details" className="mt-4">
              <div className="space-y-4">
                {/* 技術細節 */}
                {contentFilter.showTechnicalDetails && renderCollapsibleSection(
                  'technicalDetails',
                  '技術細節',
                  <Zap className="h-4 w-4" />,
                  explanation.technicalDetails,
                  '技術規格'
                )}

                {/* 相關概念 */}
                {contentFilter.showRelatedConcepts && renderCollapsibleSection(
                  'relatedConcepts',
                  '相關概念',
                  <BookOpen className="h-4 w-4" />,
                  explanation.relatedConcepts,
                  '延伸學習'
                )}

                {/* 標準符合性 */}
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Info className="h-4 w-4" />
                    <span className="font-medium">標準符合性</span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    本實現完全符合 3GPP TS 38.331 標準，並達到論文研究級精度要求。
                    所有計算方法和參數設定都基於最新的國際標準和最佳實踐。
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="interactive" className="mt-4">
              <div className="space-y-4">
                {/* 互動提示 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Eye className="h-4 w-4" />
                        視覺化提示
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2 text-sm">
                        <li>• 將滑鼠懸停在圖表元素上查看詳細資訊</li>
                        <li>• 點擊圖例項目可隱藏/顯示對應數據</li>
                        <li>• 使用縮放功能查看特定時間範圍</li>
                        <li>• 觀察顏色變化了解狀態轉換</li>
                      </ul>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Target className="h-4 w-4" />
                        參數調整
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2 text-sm">
                        <li>• 調整門檻值觀察觸發條件變化</li>
                        <li>• 修改測量間隔影響數據更新頻率</li>
                        <li>• 切換顯示選項控制圖表內容</li>
                        <li>• 使用重置按鈕恢復預設設定</li>
                      </ul>
                    </CardContent>
                  </Card>
                </div>

                {/* 快速操作指南 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">快速操作指南</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="font-medium mb-2">開始測量</div>
                        <div className="text-muted-foreground">
                          點擊「開始測量」按鈕啟動實時數據收集和事件監控
                        </div>
                      </div>
                      <div>
                        <div className="font-medium mb-2">參數配置</div>
                        <div className="text-muted-foreground">
                          在參數面板中調整門檻值、間隔等設定以符合測試需求
                        </div>
                      </div>
                      <div>
                        <div className="font-medium mb-2">數據分析</div>
                        <div className="text-muted-foreground">
                          查看歷史標籤頁分析事件觸發模式和系統性能
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}

// 說明觸發按鈕組件
export const ExplanationTrigger: React.FC<{
  chartType: 'A4' | 'D1' | 'D2' | 'T1' | 'SIB19'
  onTrigger: () => void
  className?: string
}> = ({ chartType, onTrigger, className = '' }) => {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            onClick={onTrigger}
            className={`${className}`}
          >
            <HelpCircle className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>查看 {chartType} 事件說明</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

export default ChartExplanationSystem
