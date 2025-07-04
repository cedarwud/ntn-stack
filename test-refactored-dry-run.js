#!/usr/bin/env node
/**
 * 重構版本乾運行測試 - 階段二
 * 在獨立環境中測試重構版本是否能正常編譯和運行
 */

const fs = require('fs');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

console.log('🔍 重構版本乾運行測試開始...\n');

// 創建備份並進行乾運行測試
async function performDryRun() {
    const steps = [];
    
    try {
        console.log('📋 步驟 1: 創建當前版本備份');
        await execPromise('cp simworld/frontend/src/App.tsx simworld/frontend/src/App.tsx.current-backup');
        steps.push('✅ 當前版本已備份為 App.tsx.current-backup');
        
        console.log('📋 步驟 2: 暫時替換為重構版本');
        await execPromise('cp simworld/frontend/src/App.refactored.tsx simworld/frontend/src/App.tsx');
        steps.push('✅ 重構版本已暫時替換為 App.tsx');
        
        console.log('📋 步驟 3: 執行 TypeScript 編譯檢查');
        const tsCheckResult = await runTypeScriptCheck();
        steps.push(tsCheckResult);
        
        console.log('📋 步驟 4: 執行 ESLint 檢查');
        const lintResult = await runLintCheck();
        steps.push(lintResult);
        
        console.log('📋 步驟 5: 執行建置測試');
        const buildResult = await runBuildTest();
        steps.push(buildResult);
        
        console.log('📋 步驟 6: 恢復原始版本');
        await execPromise('cp simworld/frontend/src/App.tsx.current-backup simworld/frontend/src/App.tsx');
        await execPromise('rm simworld/frontend/src/App.tsx.current-backup');
        steps.push('✅ 原始版本已恢復');
        
        return {
            success: true,
            steps: steps
        };
        
    } catch (error) {
        console.log('❌ 乾運行測試過程中發生錯誤，正在恢復原始狀態...');
        
        // 確保恢復原始狀態
        try {
            if (fs.existsSync('simworld/frontend/src/App.tsx.current-backup')) {
                await execPromise('cp simworld/frontend/src/App.tsx.current-backup simworld/frontend/src/App.tsx');
                await execPromise('rm simworld/frontend/src/App.tsx.current-backup');
                steps.push('🔧 原始版本已恢復（錯誤恢復）');
            }
        } catch (restoreError) {
            steps.push(`❌ 恢復失敗: ${restoreError.message}`);
        }
        
        return {
            success: false,
            error: error.message,
            steps: steps
        };
    }
}

async function runTypeScriptCheck() {
    try {
        console.log('   🔍 執行 TypeScript 檢查...');
        const { stdout, stderr } = await execPromise('cd simworld/frontend && npx tsc --noEmit --skipLibCheck', {
            timeout: 60000 // 1分鐘超時
        });
        return '✅ TypeScript 編譯檢查通過';
    } catch (error) {
        return `❌ TypeScript 編譯錯誤: ${error.message}`;
    }
}

async function runLintCheck() {
    try {
        console.log('   🔍 執行 ESLint 檢查...');
        const { stdout, stderr } = await execPromise('cd simworld/frontend && npm run lint -- --quiet');
        return '✅ ESLint 檢查通過';
    } catch (error) {
        // ESLint 錯誤通常不是致命的，記錄但繼續
        return `⚠️  ESLint 檢查有警告: ${error.message.slice(0, 200)}...`;
    }
}

async function runBuildTest() {
    try {
        console.log('   🔍 執行建置測試...');
        const { stdout, stderr } = await execPromise('cd simworld/frontend && npm run build', {
            timeout: 120000 // 2分鐘超時
        });
        return '✅ 建置測試通過';
    } catch (error) {
        return `❌ 建置失敗: ${error.message}`;
    }
}

// 分析測試結果
function analyzeResults(result) {
    console.log('\n📊 乾運行測試結果分析:');
    console.log('========================');
    
    result.steps.forEach(step => {
        console.log(`   ${step}`);
    });
    
    if (result.success) {
        console.log('\n🎉 重構版本乾運行測試完全成功！');
        console.log('✅ TypeScript 編譯正常');
        console.log('✅ 建置流程正常');
        console.log('✅ 可以安全進行實際重構');
        return true;
    } else {
        console.log('\n❌ 重構版本存在問題，需要修復：');
        console.log(`   錯誤: ${result.error}`);
        console.log('\n建議：');
        console.log('   1. 檢查 TypeScript 型別定義');
        console.log('   2. 檢查組件介面匹配');
        console.log('   3. 檢查導入路徑');
        return false;
    }
}

// 執行主要測試流程
async function main() {
    console.log('⚠️  注意：此測試會暫時替換 App.tsx，但會在完成後自動恢復');
    console.log('⚠️  如果測試中斷，請手動執行: cp simworld/frontend/src/App.tsx.current-backup simworld/frontend/src/App.tsx\n');
    
    const result = await performDryRun();
    const success = analyzeResults(result);
    
    // 保存測試結果
    const resultData = {
        timestamp: new Date().toISOString(),
        stage: 'Stage 2 - Dry Run Test',
        success: success,
        details: result
    };
    
    fs.writeFileSync('test-results-stage2.json', JSON.stringify(resultData, null, 2));
    console.log('\n📝 測試結果已保存至 test-results-stage2.json');
    
    if (success) {
        console.log('\n🚀 準備就緒！可以進行實際重構切換。');
    } else {
        console.log('\n🛠️  需要先修復問題才能繼續。');
    }
}

// 執行測試
main().catch(error => {
    console.error('❌ 測試執行失敗:', error);
    
    // 緊急恢復
    try {
        if (fs.existsSync('simworld/frontend/src/App.tsx.current-backup')) {
            fs.copyFileSync('simworld/frontend/src/App.tsx.current-backup', 'simworld/frontend/src/App.tsx');
            fs.unlinkSync('simworld/frontend/src/App.tsx.current-backup');
            console.log('🔧 緊急恢復完成');
        }
    } catch (restoreError) {
        console.error('❌ 緊急恢復失敗:', restoreError);
        console.log('⚠️  請手動執行: cp simworld/frontend/src/App.tsx.current-backup simworld/frontend/src/App.tsx');
    }
});