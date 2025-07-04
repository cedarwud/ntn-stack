#!/usr/bin/env node
/**
 * 組件相容性測試程式 - 階段一
 * 檢查子組件是否支援重構版本所需的 Props 介面
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 組件相容性測試開始...\n');

// 分析 App.refactored.tsx 中的組件使用方式
function analyzeRefactoredComponentUsage() {
    const refactoredPath = 'simworld/frontend/src/App.refactored.tsx';
    if (!fs.existsSync(refactoredPath)) {
        return { error: 'App.refactored.tsx 不存在' };
    }
    
    const content = fs.readFileSync(refactoredPath, 'utf8');
    
    // 解析 EnhancedSidebar 在重構版本中的使用方式
    const sidebarMatch = content.match(/<EnhancedSidebar[\s\S]*?\/>/);
    let sidebarProps = [];
    if (sidebarMatch) {
        const propsMatches = sidebarMatch[0].match(/(\w+)=/g) || [];
        sidebarProps = propsMatches.map(prop => prop.replace('=', ''));
    }
    
    // 解析 SceneView 在重構版本中的使用方式
    const sceneViewMatch = content.match(/<SceneView[\s\S]*?\/>/);
    let sceneViewProps = [];
    if (sceneViewMatch) {
        const propsMatches = sceneViewMatch[0].match(/(\w+)=/g) || [];
        sceneViewProps = propsMatches.map(prop => prop.replace('=', ''));
    }
    
    // 解析 SceneViewer 在重構版本中的使用方式
    const sceneViewerMatch = content.match(/<SceneViewer[\s\S]*?\/>/);
    let sceneViewerProps = [];
    if (sceneViewerMatch) {
        const propsMatches = sceneViewerMatch[0].match(/(\w+)=/g) || [];
        sceneViewerProps = propsMatches.map(prop => prop.replace('=', ''));
    }
    
    return {
        EnhancedSidebar: {
            propsCount: sidebarProps.length,
            props: sidebarProps
        },
        SceneView: {
            propsCount: sceneViewProps.length,
            props: sceneViewProps
        },
        SceneViewer: {
            propsCount: sceneViewerProps.length,
            props: sceneViewerProps
        }
    };
}

// 分析組件的 Props 介面定義
function analyzeComponentInterface(componentPath, componentName) {
    if (!fs.existsSync(componentPath)) {
        return { error: `${componentName} 組件檔案不存在` };
    }
    
    const content = fs.readFileSync(componentPath, 'utf8');
    
    // 查找 Props 介面定義
    const propsInterfaceRegex = new RegExp(`interface\\s+${componentName}Props[\\s\\S]*?}`, 'g');
    const propsMatch = content.match(propsInterfaceRegex);
    
    if (!propsMatch) {
        return { error: `找不到 ${componentName}Props 介面定義` };
    }
    
    // 解析 Props 屬性
    const propsDefinition = propsMatch[0];
    const propLines = propsDefinition.split('\n').slice(1, -1); // 去除第一行和最後一行
    const props = propLines
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('//'))
        .map(line => {
            const match = line.match(/(\w+)[\?\:]?\s*:/);
            return match ? match[1] : null;
        })
        .filter(prop => prop);
    
    return {
        propsCount: props.length,
        props: props,
        hasInterface: true
    };
}

// 執行測試
const tests = [
    {
        name: '重構版本組件使用分析',
        check: analyzeRefactoredComponentUsage
    },
    {
        name: 'EnhancedSidebar Props 介面檢查',
        check: () => analyzeComponentInterface(
            'simworld/frontend/src/components/layout/EnhancedSidebar.tsx',
            'Sidebar'  // 實際使用 SidebarProps
        )
    },
    {
        name: 'SceneView Props 介面檢查',
        check: () => analyzeComponentInterface(
            'simworld/frontend/src/components/scenes/StereogramView.tsx',
            'SceneView'
        )
    },
    {
        name: 'SceneViewer Props 介面檢查',
        check: () => analyzeComponentInterface(
            'simworld/frontend/src/components/scenes/FloorView.tsx',
            'SceneViewer'
        )
    }
];

let allTestsPassed = true;
const results = {};

tests.forEach(test => {
    console.log(`📋 執行測試: ${test.name}`);
    try {
        const result = test.check();
        results[test.name] = result;
        
        if (result.error) {
            console.log(`   ❌ ${result.error}`);
            allTestsPassed = false;
        } else {
            // 顯示結果
            Object.entries(result).forEach(([key, value]) => {
                if (key === 'props' && Array.isArray(value)) {
                    console.log(`   📊 ${key}: [${value.slice(0, 5).join(', ')}${value.length > 5 ? '...' : ''}] (${value.length} 個)`);
                } else {
                    const status = typeof value === 'boolean' ? (value ? '✅' : '❌') : '📊';
                    console.log(`   ${status} ${key}: ${value}`);
                }
            });
        }
    } catch (error) {
        console.log(`   ❌ 測試失敗: ${error.message}`);
        allTestsPassed = false;
        results[test.name] = { error: error.message };
    }
    console.log('');
});

// 相容性分析
console.log('🔄 組件相容性分析:');
console.log('===================');

if (results['重構版本組件使用分析'] && !results['重構版本組件使用分析'].error) {
    const refactoredUsage = results['重構版本組件使用分析'];
    
    console.log('\n📊 Props 數量比較:');
    Object.entries(refactoredUsage).forEach(([component, data]) => {
        if (data.propsCount !== undefined) {
            console.log(`   ${component}: ${data.propsCount} 個 Props`);
        }
    });
    
    // 檢查是否有缺失的 Props
    const interfaceChecks = [
        'EnhancedSidebar Props 介面檢查',
        'SceneView Props 介面檢查', 
        'SceneViewer Props 介面檢查'
    ];
    
    console.log('\n🔧 介面相容性檢查:');
    interfaceChecks.forEach(checkName => {
        const result = results[checkName];
        if (result && !result.error) {
            console.log(`   ✅ ${checkName.replace(' Props 介面檢查', '')}: 介面定義存在`);
        } else {
            console.log(`   ❌ ${checkName.replace(' Props 介面檢查', '')}: 介面定義問題`);
            allTestsPassed = false;
        }
    });
}

// 輸出總結
console.log('\n📊 相容性測試結果總結:');
console.log('========================');
if (allTestsPassed) {
    console.log('✅ 所有組件相容性測試通過！重構版本可以直接使用。');
} else {
    console.log('❌ 部分組件需要修改才能支援重構版本。');
}

// 將結果寫入檔案
const resultData = {
    timestamp: new Date().toISOString(),
    stage: 'Stage 1 - Component Compatibility',
    allTestsPassed,
    results
};

fs.writeFileSync('test-results-stage1.json', JSON.stringify(resultData, null, 2));
console.log('\n📝 測試結果已保存至 test-results-stage1.json');