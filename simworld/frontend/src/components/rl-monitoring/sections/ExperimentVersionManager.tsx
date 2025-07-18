/**
 * 訓練版本管理組件
 * 提供訓練配置的保存、載入、比較和回滾功能
 */

import React, { useState, useCallback, useEffect } from 'react';
import './ExperimentVersionManager.scss';

interface ExperimentVersion {
    id: string;
    name: string;
    description: string;
    config: any;
    created_at: string;
    created_by: string;
    tags: string[];
    performance_summary?: {
        average_reward: number;
        success_rate: number;
        convergence_episodes: number;
    };
    is_baseline: boolean;
    parent_version?: string;
}

interface ExperimentVersionManagerProps {
    currentConfig: any;
    onConfigLoad: (config: any) => void;
    onConfigSave?: (version: ExperimentVersion) => void;
}

const ExperimentVersionManager: React.FC<ExperimentVersionManagerProps> = ({
    currentConfig,
    onConfigLoad,
    onConfigSave
}) => {
    const [versions, setVersions] = useState<ExperimentVersion[]>([]);
    const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
    const [activeView, setActiveView] = useState<string>('list');
    const [isLoading, setIsLoading] = useState(true);
    const [saveDialogOpen, setSaveDialogOpen] = useState(false);
    const [newVersionData, setNewVersionData] = useState({
        name: '',
        description: '',
        tags: [] as string[],
        is_baseline: false
    });

    // 載入版本列表
    const loadVersions = useCallback(async () => {
        setIsLoading(true);
        try {
            // 模擬 API 調用
            const mockVersions: ExperimentVersion[] = [
                {
                    id: 'v1.0.0',
                    name: '基準訓練 v1.0',
                    description: '初始基準配置，使用標準 DQN 算法',
                    config: {
                        algorithm: 'dqn',
                        learning_rate: 0.001,
                        epsilon_start: 1.0,
                        epsilon_decay: 0.995
                    },
                    created_at: '2025-07-15T10:00:00Z',
                    created_by: 'researcher@example.com',
                    tags: ['baseline', 'dqn', 'stable'],
                    performance_summary: {
                        average_reward: 85.2,
                        success_rate: 0.78,
                        convergence_episodes: 1200
                    },
                    is_baseline: true
                },
                {
                    id: 'v1.1.0',
                    name: '優化學習率訓練',
                    description: '調整學習率參數，提升收斂速度',
                    config: {
                        algorithm: 'dqn',
                        learning_rate: 0.002,
                        epsilon_start: 1.0,
                        epsilon_decay: 0.995
                    },
                    created_at: '2025-07-16T14:30:00Z',
                    created_by: 'researcher@example.com',
                    tags: ['optimization', 'learning-rate', 'experimental'],
                    performance_summary: {
                        average_reward: 92.1,
                        success_rate: 0.82,
                        convergence_episodes: 950
                    },
                    is_baseline: false,
                    parent_version: 'v1.0.0'
                },
                {
                    id: 'v1.2.0',
                    name: '都市場景特化配置',
                    description: '針對都市高密度環境的特化參數配置',
                    config: {
                        algorithm: 'ddqn',
                        learning_rate: 0.0005,
                        epsilon_start: 0.9,
                        epsilon_decay: 0.99,
                        scenario_type: 'urban'
                    },
                    created_at: '2025-07-17T09:15:00Z',
                    created_by: 'researcher@example.com',
                    tags: ['urban', 'ddqn', 'specialized'],
                    performance_summary: {
                        average_reward: 96.8,
                        success_rate: 0.89,
                        convergence_episodes: 800
                    },
                    is_baseline: false,
                    parent_version: 'v1.1.0'
                }
            ];

            setVersions(mockVersions);
        } catch (error) {
            console.error('載入版本列表失敗:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // 保存當前配置為新版本
    const saveCurrentConfig = useCallback(async () => {
        if (!newVersionData.name.trim()) {
            alert('請輸入版本名稱');
            return;
        }

        const newVersion: ExperimentVersion = {
            id: `v${versions.length + 1}.0.0`,
            name: newVersionData.name,
            description: newVersionData.description,
            config: { ...currentConfig },
            created_at: new Date().toISOString(),
            created_by: 'current_user@example.com',
            tags: newVersionData.tags,
            is_baseline: newVersionData.is_baseline
        };

        try {
            // 模擬 API 保存
            setVersions(prev => [newVersion, ...prev]);
            
            if (onConfigSave) {
                onConfigSave(newVersion);
            }

            // 重置表單
            setNewVersionData({
                name: '',
                description: '',
                tags: [],
                is_baseline: false
            });
            setSaveDialogOpen(false);

            console.log('✅ 版本保存成功:', newVersion.id);
        } catch (error) {
            console.error('保存版本失敗:', error);
        }
    }, [currentConfig, newVersionData, versions.length, onConfigSave]);

    // 載入指定版本的配置
    const loadVersion = useCallback((versionId: string) => {
        const version = versions.find(v => v.id === versionId);
        if (version) {
            onConfigLoad(version.config);
            console.log('✅ 已載入版本:', version.name);
        }
    }, [versions, onConfigLoad]);

    // 刪除版本
    const deleteVersion = useCallback((versionId: string) => {
        if (window.confirm('確定要刪除此版本嗎？此操作無法撤銷。')) {
            setVersions(prev => prev.filter(v => v.id !== versionId));
            console.log('🗑️ 已刪除版本:', versionId);
        }
    }, []);

    // 比較版本
    const compareVersions = useCallback(() => {
        if (selectedVersions.length < 2) {
            alert('請選擇至少兩個版本進行比較');
            return;
        }
        setActiveView('compare');
    }, [selectedVersions]);

    // 格式化日期
    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('zh-TW');
    };

    // 獲取性能變化指示器
    const getPerformanceIndicator = (current: number, baseline: number) => {
        const change = ((current - baseline) / baseline) * 100;
        if (change > 5) return { icon: '📈', color: '#10b981', text: `+${change.toFixed(1)}%` };
        if (change < -5) return { icon: '📉', color: '#ef4444', text: `${change.toFixed(1)}%` };
        return { icon: '➡️', color: '#6b7280', text: `${change.toFixed(1)}%` };
    };

    useEffect(() => {
        loadVersions();
    }, [loadVersions]);

    if (isLoading) {
        return (
            <div className="version-manager-loading">
                <div className="loading-spinner">🔄</div>
                <p>載入版本列表中...</p>
            </div>
        );
    }

    return (
        <div className="experiment-version-manager">
            <div className="manager-header">
                <h3>📚 訓練版本管理</h3>
                <div className="header-actions">
                    <button
                        className="btn btn-primary"
                        onClick={() => setSaveDialogOpen(true)}
                    >
                        💾 保存當前配置
                    </button>
                    <button
                        className="btn btn-secondary"
                        onClick={loadVersions}
                    >
                        🔄 重新載入
                    </button>
                </div>
            </div>

            <div className="manager-tabs">
                <div className="tab-nav">
                    <button
                        className={`tab-btn ${activeView === 'list' ? 'active' : ''}`}
                        onClick={() => setActiveView('list')}
                    >
                        📋 版本列表
                    </button>
                    <button
                        className={`tab-btn ${activeView === 'compare' ? 'active' : ''}`}
                        onClick={() => setActiveView('compare')}
                        disabled={selectedVersions.length < 2}
                    >
                        🔍 版本比較
                    </button>
                    <button
                        className={`tab-btn ${activeView === 'timeline' ? 'active' : ''}`}
                        onClick={() => setActiveView('timeline')}
                    >
                        📈 發展時間線
                    </button>
                </div>

                <div className="tab-content">
                    {activeView === 'list' && (
                        <div className="version-list">
                            <div className="list-controls">
                                <div className="selection-info">
                                    已選擇 {selectedVersions.length} 個版本
                                </div>
                                <div className="list-actions">
                                    {selectedVersions.length >= 2 && (
                                        <button
                                            className="btn btn-info btn-sm"
                                            onClick={compareVersions}
                                        >
                                            🔍 比較選中版本
                                        </button>
                                    )}
                                    {selectedVersions.length > 0 && (
                                        <button
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => setSelectedVersions([])}
                                        >
                                            ❌ 清除選擇
                                        </button>
                                    )}
                                </div>
                            </div>

                            <div className="versions-grid">
                                {versions.map(version => (
                                    <div
                                        key={version.id}
                                        className={`version-card ${selectedVersions.includes(version.id) ? 'selected' : ''}`}
                                    >
                                        <div className="version-header">
                                            <div className="version-info">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedVersions.includes(version.id)}
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setSelectedVersions(prev => [...prev, version.id]);
                                                        } else {
                                                            setSelectedVersions(prev => prev.filter(id => id !== version.id));
                                                        }
                                                    }}
                                                />
                                                <div className="version-title">
                                                    <h4>{version.name}</h4>
                                                    <span className="version-id">{version.id}</span>
                                                    {version.is_baseline && (
                                                        <span className="baseline-badge">基準</span>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="version-actions">
                                                <button
                                                    className="btn btn-sm btn-primary"
                                                    onClick={() => loadVersion(version.id)}
                                                >
                                                    📥 載入
                                                </button>
                                                {!version.is_baseline && (
                                                    <button
                                                        className="btn btn-sm btn-danger"
                                                        onClick={() => deleteVersion(version.id)}
                                                    >
                                                        🗑️
                                                    </button>
                                                )}
                                            </div>
                                        </div>

                                        <div className="version-content">
                                            <p className="version-description">{version.description}</p>
                                            
                                            <div className="version-tags">
                                                {version.tags.map(tag => (
                                                    <span key={tag} className="tag">{tag}</span>
                                                ))}
                                            </div>

                                            {version.performance_summary && (
                                                <div className="performance-summary">
                                                    <div className="perf-item">
                                                        <span>平均獎勵:</span>
                                                        <span>{version.performance_summary.average_reward.toFixed(1)}</span>
                                                    </div>
                                                    <div className="perf-item">
                                                        <span>成功率:</span>
                                                        <span>{(version.performance_summary.success_rate * 100).toFixed(1)}%</span>
                                                    </div>
                                                    <div className="perf-item">
                                                        <span>收斂回合:</span>
                                                        <span>{version.performance_summary.convergence_episodes}</span>
                                                    </div>
                                                </div>
                                            )}

                                            <div className="version-meta">
                                                <span>創建時間: {formatDate(version.created_at)}</span>
                                                <span>創建者: {version.created_by}</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* 保存對話框 */}
            {saveDialogOpen && (
                <div className="save-dialog-overlay">
                    <div className="save-dialog">
                        <div className="dialog-header">
                            <h4>💾 保存訓練版本</h4>
                            <button
                                className="close-btn"
                                onClick={() => setSaveDialogOpen(false)}
                            >
                                ❌
                            </button>
                        </div>
                        
                        <div className="dialog-content">
                            <div className="form-group">
                                <label>版本名稱 *</label>
                                <input
                                    type="text"
                                    value={newVersionData.name}
                                    onChange={(e) => setNewVersionData(prev => ({
                                        ...prev,
                                        name: e.target.value
                                    }))}
                                    placeholder="例如：優化學習率訓練 v2.0"
                                />
                            </div>
                            
                            <div className="form-group">
                                <label>版本描述</label>
                                <textarea
                                    value={newVersionData.description}
                                    onChange={(e) => setNewVersionData(prev => ({
                                        ...prev,
                                        description: e.target.value
                                    }))}
                                    placeholder="描述此版本的主要變更和目標..."
                                    rows={3}
                                />
                            </div>
                            
                            <div className="form-group">
                                <label>標籤</label>
                                <input
                                    type="text"
                                    placeholder="用逗號分隔，例如：experimental, optimization, urban"
                                    onChange={(e) => setNewVersionData(prev => ({
                                        ...prev,
                                        tags: e.target.value.split(',').map(tag => tag.trim()).filter(Boolean)
                                    }))}
                                />
                            </div>
                            
                            <div className="form-group">
                                <label className="checkbox-label">
                                    <input
                                        type="checkbox"
                                        checked={newVersionData.is_baseline}
                                        onChange={(e) => setNewVersionData(prev => ({
                                            ...prev,
                                            is_baseline: e.target.checked
                                        }))}
                                    />
                                    設為基準版本
                                </label>
                            </div>
                        </div>
                        
                        <div className="dialog-actions">
                            <button
                                className="btn btn-secondary"
                                onClick={() => setSaveDialogOpen(false)}
                            >
                                取消
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={saveCurrentConfig}
                            >
                                💾 保存版本
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ExperimentVersionManager;
