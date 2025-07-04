#!/usr/bin/env node
/**
 * App.tsx 功能基準測試程式
 * 用於確保重構過程中所有功能保持正常
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 App.tsx 功能基準測試開始...\n');

// 測試項目清單
const tests = [
    {
        name: '檔案存在性檢查',
        check: () => {
            const appPath = 'simworld/frontend/src/App.tsx';
            const refactoredPath = 'simworld/frontend/src/App.refactored.tsx';
            const backupPath = 'simworld/frontend/src/App.tsx.stage3-backup';
            
            return {
                'App.tsx 存在': fs.existsSync(appPath),
                'App.refactored.tsx 已清理': !fs.existsSync(refactoredPath), // 重構完成後應該被清理
                'App.tsx.stage3-backup 已移除': !fs.existsSync(backupPath), // 改為檢查已移除
                'App.tsx 大小': fs.existsSync(appPath) ? fs.statSync(appPath).size : 0,
                'App.legacy.tsx 備份存在': fs.existsSync('simworld/frontend/src/App.legacy.tsx')
            };
        }
    },
    {
        name: 'useState Hook 數量檢查',
        check: () => {
            const appPath = 'simworld/frontend/src/App.tsx';
            if (!fs.existsSync(appPath)) return { error: 'App.tsx 不存在' };
            
            const content = fs.readFileSync(appPath, 'utf8');
            const useStateMatches = content.match(/useState\s*\(/g) || [];
            const useCallbackMatches = content.match(/useCallback\s*\(/g) || [];
            const useMemoMatches = content.match(/useMemo\s*\(/g) || [];
            
            return {
                'useState 數量': useStateMatches.length,
                'useCallback 數量': useCallbackMatches.length,
                'useMemo 數量': useMemoMatches.length
            };
        }
    },
    {
        name: 'Props 傳遞複雜度檢查',
        check: () => {
            const appPath = 'simworld/frontend/src/App.tsx';
            if (!fs.existsSync(appPath)) return { error: 'App.tsx 不存在' };
            
            const content = fs.readFileSync(appPath, 'utf8');
            
            // 檢查 EnhancedSidebar 的 props 數量
            const sidebarMatch = content.match(/<EnhancedSidebar[\s\S]*?\/>/);
            let sidebarPropsCount = 0;
            if (sidebarMatch) {
                const propsMatches = sidebarMatch[0].match(/\w+=/g) || [];
                sidebarPropsCount = propsMatches.length;
            }
            
            // 檢查 SceneView 的 props 數量
            const sceneViewMatch = content.match(/<SceneView[\s\S]*?\/>/);
            let sceneViewPropsCount = 0;
            if (sceneViewMatch) {
                const propsMatches = sceneViewMatch[0].match(/\w+=/g) || [];
                sceneViewPropsCount = propsMatches.length;
            }
            
            return {
                'EnhancedSidebar Props 數量': sidebarPropsCount,
                'SceneView Props 數量': sceneViewPropsCount
            };
        }
    },
    {
        name: '關鍵功能模組檢查',
        check: () => {
            const appPath = 'simworld/frontend/src/App.tsx';
            if (!fs.existsSync(appPath)) return { error: 'App.tsx 不存在' };
            
            const content = fs.readFileSync(appPath, 'utf8');
            
            return {
                '設備管理功能': content.includes('useDevices') && content.includes('tempDevices'),
                '衛星控制功能': content.includes('satelliteState') || content.includes('satelliteEnabled'),
                '換手機制功能': content.includes('handoverState') || content.includes('useHandoverState'),
                'UI控制功能': content.includes('uiState') && content.includes('activeComponent'),
                '3D/2D場景功能': content.includes('SceneView') && content.includes('SceneViewer'),
                '階段功能開關': content.includes('featureState') || content.includes('useFeatureState')
            };
        }
    },
    {
        name: '依賴陣列複雜度檢查',
        check: () => {
            const appPath = 'simworld/frontend/src/App.tsx';
            if (!fs.existsSync(appPath)) return { error: 'App.tsx 不存在' };
            
            const content = fs.readFileSync(appPath, 'utf8');
            
            // 查找 renderActiveComponent 的依賴陣列
            const renderMatch = content.match(/renderActiveComponent[\s\S]*?\], \[([^\]]*)\]/);
            let dependencyCount = 0;
            if (renderMatch) {
                const dependencies = renderMatch[1].split(',').filter(dep => dep.trim().length > 0);
                dependencyCount = dependencies.length;
            }
            
            return {
                'renderActiveComponent 依賴數量': dependencyCount,
                'renderActiveComponent 存在': content.includes('renderActiveComponent')
            };
        }
    }
];

// 執行測試
let allTestsPassed = true;
const results = {};

tests.forEach(test => {
    console.log(`📋 執行測試: ${test.name}`);
    try {
        const result = test.check();
        results[test.name] = result;
        
        // 顯示結果
        Object.entries(result).forEach(([key, value]) => {
            const status = typeof value === 'boolean' ? (value ? '✅' : '❌') : '📊';
            console.log(`   ${status} ${key}: ${value}`);
        });
        
        // 檢查是否有錯誤或失敗
        if (result.error || Object.values(result).some(v => v === false)) {
            allTestsPassed = false;
        }
    } catch (error) {
        console.log(`   ❌ 測試失敗: ${error.message}`);
        allTestsPassed = false;
        results[test.name] = { error: error.message };
    }
    console.log('');
});

// 輸出總結
console.log('📊 測試結果總結:');
console.log('================');
if (allTestsPassed) {
    console.log('✅ 所有基準測試通過！可以安全進行下一步。');
} else {
    console.log('❌ 部分測試失敗，需要先修復問題才能繼續。');
}

// 將結果寫入檔案
const resultData = {
    timestamp: new Date().toISOString(),
    stage: 'Stage 0 - Baseline',
    allTestsPassed,
    results
};

fs.writeFileSync('test-results-stage0.json', JSON.stringify(resultData, null, 2));
console.log('\n📝 測試結果已保存至 test-results-stage0.json');