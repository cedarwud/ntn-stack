#!/usr/bin/env node
/**
 * 最終切換確認程式 - 階段三
 * 進行實際重構切換前的最後檢查和準備
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 最終切換確認檢查開始...\n');

// 檢查所有先決條件
function checkPrerequisites() {
    const checks = [
        {
            name: '檔案存在性檢查',
            check: () => {
                const currentExists = fs.existsSync('simworld/frontend/src/App.tsx');
                const refactoredExists = fs.existsSync('simworld/frontend/src/App.refactored.tsx');
                const backupNotExists = !fs.existsSync('simworld/frontend/src/App.tsx.stage3-backup');
                
                return {
                    '當前版本存在': currentExists,
                    '重構版本存在': refactoredExists,
                    '冗餘備份已清理': backupNotExists,
                    '所有檔案就緒': currentExists && refactoredExists && backupNotExists
                };
            }
        },
        {
            name: '測試結果驗證',
            check: () => {
                const stage0Results = fs.existsSync('test-results-stage0.json') 
                    ? JSON.parse(fs.readFileSync('test-results-stage0.json', 'utf8'))
                    : null;
                    
                const stage1Results = fs.existsSync('test-results-stage1.json')
                    ? JSON.parse(fs.readFileSync('test-results-stage1.json', 'utf8'))
                    : null;
                    
                const stage2Results = fs.existsSync('test-results-stage2.json')
                    ? JSON.parse(fs.readFileSync('test-results-stage2.json', 'utf8'))
                    : null;
                
                return {
                    '階段零測試通過': stage0Results?.allTestsPassed || false,
                    '階段一測試通過': stage1Results?.allTestsPassed || false,
                    '階段二測試通過': stage2Results?.success || false,
                    '所有測試通過': (stage0Results?.allTestsPassed && stage1Results?.allTestsPassed && stage2Results?.success) || false
                };
            }
        },
        {
            name: '檔案大小比較',
            check: () => {
                const currentSize = fs.existsSync('simworld/frontend/src/App.tsx') 
                    ? fs.statSync('simworld/frontend/src/App.tsx').size 
                    : 0;
                    
                const refactoredSize = fs.existsSync('simworld/frontend/src/App.refactored.tsx')
                    ? fs.statSync('simworld/frontend/src/App.refactored.tsx').size
                    : 0;
                
                const reduction = currentSize > 0 ? ((currentSize - refactoredSize) / currentSize * 100).toFixed(1) : 0;
                
                return {
                    '當前版本大小': `${currentSize} bytes`,
                    '重構版本大小': `${refactoredSize} bytes`,
                    '減少百分比': `${reduction}%`,
                    '顯著減少': parseFloat(reduction) > 60
                };
            }
        },
        {
            name: 'Context 架構檢查',
            check: () => {
                const contexts = [
                    'simworld/frontend/src/contexts/AppStateContext.tsx',
                    'simworld/frontend/src/contexts/DataSyncContext.tsx',
                    'simworld/frontend/src/contexts/StrategyContext.tsx'
                ];
                
                const contextExists = contexts.map(path => ({
                    [path.split('/').pop()]: fs.existsSync(path)
                }));
                
                const allContextsExist = contexts.every(path => fs.existsSync(path));
                
                return {
                    ...Object.assign({}, ...contextExists),
                    '所有Context就緒': allContextsExist
                };
            }
        }
    ];
    
    let allChecksPass = true;
    const results = {};
    
    checks.forEach(check => {
        console.log(`📋 執行檢查: ${check.name}`);
        try {
            const result = check.check();
            results[check.name] = result;
            
            Object.entries(result).forEach(([key, value]) => {
                const status = typeof value === 'boolean' ? (value ? '✅' : '❌') : '📊';
                console.log(`   ${status} ${key}: ${value}`);
                
                if (typeof value === 'boolean' && !value) {
                    allChecksPass = false;
                }
            });
        } catch (error) {
            console.log(`   ❌ 檢查失敗: ${error.message}`);
            allChecksPass = false;
            results[check.name] = { error: error.message };
        }
        console.log('');
    });
    
    return { allChecksPass, results };
}

// 生成切換計畫
function generateSwitchPlan() {
    console.log('📋 生成切換執行計畫:');
    console.log('====================');
    
    const plan = [
        {
            step: 1,
            action: '建立最終備份',
            command: 'cp simworld/frontend/src/App.tsx simworld/frontend/src/App.legacy.tsx',
            description: '將當前版本保存為 App.legacy.tsx'
        },
        {
            step: 2,
            action: '執行切換',
            command: 'cp simworld/frontend/src/App.refactored.tsx simworld/frontend/src/App.tsx',
            description: '將重構版本設為新的主版本'
        },
        {
            step: 3,
            action: '清理檔案',
            command: 'rm simworld/frontend/src/App.refactored.tsx',
            description: '移除重構檔案（已合併到主版本）'
        },
        {
            step: 4,
            action: '驗證切換',
            command: 'npm run build',
            description: '執行建置驗證切換成功'
        },
        {
            step: 5,
            action: '代碼品質檢查',
            command: 'npm run lint',
            description: '修復可能的 ESLint 警告'
        }
    ];
    
    plan.forEach(item => {
        console.log(`   ${item.step}. ${item.action}`);
        console.log(`      指令: ${item.command}`);
        console.log(`      說明: ${item.description}\n`);
    });
    
    return plan;
}

// 風險評估和回滾方案
function assessRisksAndRollback() {
    console.log('⚠️  風險評估和回滾方案:');
    console.log('======================');
    
    const risks = [
        {
            risk: '編譯錯誤',
            probability: '低',
            impact: '中',
            mitigation: '乾運行測試已通過，風險極低'
        },
        {
            risk: '運行時錯誤',
            probability: '低',
            impact: '中',
            mitigation: 'Context架構已驗證，組件介面相容'
        },
        {
            risk: '效能退化',
            probability: '極低',
            impact: '低',
            mitigation: '重構減少了狀態複雜度，應該提升效能'
        }
    ];
    
    console.log('🚨 風險清單:');
    risks.forEach((risk, index) => {
        console.log(`   ${index + 1}. ${risk.risk} (機率: ${risk.probability}, 影響: ${risk.impact})`);
        console.log(`      緩解措施: ${risk.mitigation}\n`);
    });
    
    console.log('🔙 緊急回滾方案:');
    console.log('   如果切換後發現問題，執行以下指令立即回滾:');
    console.log('   cp simworld/frontend/src/App.legacy.tsx simworld/frontend/src/App.tsx\n');
}

// 主要執行函數
function main() {
    const { allChecksPass, results } = checkPrerequisites();
    
    console.log('📊 最終檢查結果總結:');
    console.log('===================');
    
    if (allChecksPass) {
        console.log('✅ 所有先決條件檢查通過！');
        console.log('✅ 重構切換已完全準備就緒');
        console.log('✅ 建議立即執行切換\n');
        
        const plan = generateSwitchPlan();
        assessRisksAndRollback();
        
        console.log('🚀 建議的下一步操作:');
        console.log('==================');
        console.log('1. 如果您同意進行切換，請執行以下指令:');
        console.log('   node execute-refactor-switch.js');
        console.log('2. 或者手動執行上述切換計畫中的步驟');
        console.log('3. 切換完成後執行測試驗證');
        
    } else {
        console.log('❌ 部分檢查未通過，需要先解決問題:');
        
        Object.entries(results).forEach(([checkName, result]) => {
            if (result.error) {
                console.log(`   ❌ ${checkName}: ${result.error}`);
            } else {
                Object.entries(result).forEach(([key, value]) => {
                    if (typeof value === 'boolean' && !value) {
                        console.log(`   ❌ ${checkName} - ${key}: 失敗`);
                    }
                });
            }
        });
    }
    
    // 保存檢查結果
    const resultData = {
        timestamp: new Date().toISOString(),
        stage: 'Stage 3 - Final Switch Confirmation',
        allChecksPass,
        ready: allChecksPass,
        results
    };
    
    fs.writeFileSync('test-results-stage3.json', JSON.stringify(resultData, null, 2));
    console.log('\n📝 檢查結果已保存至 test-results-stage3.json');
}

// 執行檢查
main();