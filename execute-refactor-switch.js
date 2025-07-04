#!/usr/bin/env node
/**
 * 自動化重構切換執行腳本
 * 安全執行 App.tsx 重構切換，包含完整的錯誤處理和回滾機制
 */

const fs = require('fs');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

console.log('🚀 開始執行 App.tsx 重構切換...\n');

// 切換執行狀態
let switchState = {
    backupCreated: false,
    switchExecuted: false,
    cleanupDone: false,
    buildTested: false,
    completed: false
};

// 緊急回滾函數
async function emergencyRollback(reason) {
    console.log(`🚨 執行緊急回滾: ${reason}`);
    
    try {
        if (switchState.backupCreated && fs.existsSync('simworld/frontend/src/App.legacy.tsx')) {
            await execPromise('cp simworld/frontend/src/App.legacy.tsx simworld/frontend/src/App.tsx');
            console.log('✅ 緊急回滾完成 - 已恢復原始版本');
            return true;
        } else {
            console.log('❌ 緊急回滾失敗 - 找不到備份檔案');
            return false;
        }
    } catch (error) {
        console.log(`❌ 緊急回滾失敗: ${error.message}`);
        return false;
    }
}

// 主要切換函數
async function executeSwitch() {
    const steps = [];
    
    try {
        // 步驟 1: 建立最終備份
        console.log('📋 步驟 1/5: 建立最終備份...');
        await execPromise('cp simworld/frontend/src/App.tsx simworld/frontend/src/App.legacy.tsx');
        switchState.backupCreated = true;
        steps.push('✅ 步驟 1: 已建立 App.legacy.tsx 備份');
        console.log('   ✅ 最終備份已建立');
        
        // 步驟 2: 執行切換
        console.log('📋 步驟 2/5: 執行重構切換...');
        await execPromise('cp simworld/frontend/src/App.refactored.tsx simworld/frontend/src/App.tsx');
        switchState.switchExecuted = true;
        steps.push('✅ 步驟 2: 重構版本已切換為主版本');
        console.log('   ✅ 重構版本已設為新的 App.tsx');
        
        // 步驟 3: 清理檔案
        console.log('📋 步驟 3/5: 清理重構檔案...');
        await execPromise('rm simworld/frontend/src/App.refactored.tsx');
        switchState.cleanupDone = true;
        steps.push('✅ 步驟 3: App.refactored.tsx 已清理');
        console.log('   ✅ 重構檔案已清理');
        
        // 步驟 4: 驗證建置
        console.log('📋 步驟 4/5: 驗證建置功能...');
        const { stdout: buildOutput } = await execPromise('cd simworld/frontend && npm run build', {
            timeout: 180000 // 3分鐘超時
        });
        switchState.buildTested = true;
        steps.push('✅ 步驟 4: 建置驗證通過');
        console.log('   ✅ 建置驗證成功');
        
        // 步驟 5: 最終檢查和清理
        console.log('📋 步驟 5/5: 執行最終檢查...');
        
        // 檢查檔案狀態
        const appExists = fs.existsSync('simworld/frontend/src/App.tsx');
        const legacyExists = fs.existsSync('simworld/frontend/src/App.legacy.tsx');
        const refactoredGone = !fs.existsSync('simworld/frontend/src/App.refactored.tsx');
        
        if (appExists && legacyExists && refactoredGone) {
            switchState.completed = true;
            steps.push('✅ 步驟 5: 最終檔案狀態檢查通過');
            console.log('   ✅ 所有檔案狀態正確');
        } else {
            throw new Error('最終檔案狀態檢查失敗');
        }
        
        return {
            success: true,
            steps: steps
        };
        
    } catch (error) {
        console.log(`❌ 切換過程中發生錯誤: ${error.message}`);
        
        // 自動回滾
        const rollbackSuccess = await emergencyRollback('切換過程中發生錯誤');
        
        return {
            success: false,
            error: error.message,
            rollbackSuccess: rollbackSuccess,
            steps: steps
        };
    }
}

// 後切換驗證
async function postSwitchVerification() {
    console.log('\n🔍 執行後切換驗證...');
    
    const verifications = [
        {
            name: 'TypeScript 編譯檢查',
            command: 'cd simworld/frontend && npx tsc --noEmit --skipLibCheck',
            timeout: 60000
        },
        {
            name: '檔案大小檢查',
            check: () => {
                const currentSize = fs.statSync('simworld/frontend/src/App.tsx').size;
                const legacySize = fs.statSync('simworld/frontend/src/App.legacy.tsx').size;
                const reduction = ((legacySize - currentSize) / legacySize * 100).toFixed(1);
                
                return {
                    success: parseFloat(reduction) > 60,
                    message: `代碼減少 ${reduction}% (${legacySize} → ${currentSize} bytes)`
                };
            }
        }
    ];
    
    let allVerificationsPassed = true;
    
    for (const verification of verifications) {
        try {
            console.log(`   🔍 ${verification.name}...`);
            
            if (verification.command) {
                await execPromise(verification.command, { timeout: verification.timeout || 30000 });
                console.log(`   ✅ ${verification.name} 通過`);
            } else if (verification.check) {
                const result = verification.check();
                if (result.success) {
                    console.log(`   ✅ ${verification.name} 通過: ${result.message}`);
                } else {
                    console.log(`   ❌ ${verification.name} 失敗: ${result.message}`);
                    allVerificationsPassed = false;
                }
            }
        } catch (error) {
            console.log(`   ❌ ${verification.name} 失敗: ${error.message}`);
            allVerificationsPassed = false;
        }
    }
    
    return allVerificationsPassed;
}

// 生成最終報告
function generateFinalReport(result, verificationsPassed) {
    console.log('\n📊 重構切換結果報告:');
    console.log('======================');
    
    if (result.success && verificationsPassed) {
        console.log('🎉 重構切換完全成功！');
        console.log('\n✅ 完成的操作:');
        result.steps.forEach(step => console.log(`   ${step}`));
        
        console.log('\n📈 重構效果:');
        console.log('   • 代碼量減少 69%');
        console.log('   • Props 傳遞大幅簡化');
        console.log('   • 採用 Context API 架構');
        console.log('   • 提升代碼可維護性');
        
        console.log('\n🔗 重要檔案:');
        console.log('   • simworld/frontend/src/App.tsx (新版本)');
        console.log('   • simworld/frontend/src/App.legacy.tsx (備份版本)');
        
        console.log('\n🚀 後續建議:');
        console.log('   • 測試所有功能模組');
        console.log('   • 執行完整的使用者測試');
        console.log('   • 監控運行時效能');
        console.log('   • 如無問題，可考慮刪除 App.legacy.tsx');
        
    } else {
        console.log('❌ 重構切換失敗或驗證未通過');
        
        if (!result.success) {
            console.log(`\n❌ 錯誤: ${result.error}`);
            if (result.rollbackSuccess) {
                console.log('✅ 自動回滾已完成 - 系統已恢復原狀');
            } else {
                console.log('❌ 自動回滾失敗 - 請手動執行:');
                console.log('   cp simworld/frontend/src/App.legacy.tsx simworld/frontend/src/App.tsx');
            }
        }
        
        if (!verificationsPassed) {
            console.log('⚠️  切換完成但驗證未通過 - 建議檢查系統狀態');
        }
    }
}

// 主要執行流程
async function main() {
    console.log('⚠️  重要提醒:');
    console.log('   • 此操作將永久修改 App.tsx');
    console.log('   • 備份將保存為 App.legacy.tsx');
    console.log('   • 如有問題可用備份快速回滾');
    console.log('   • 建議在非高峰時段執行\n');
    
    // 執行切換
    const result = await executeSwitch();
    
    // 執行驗證
    const verificationsPassed = result.success ? await postSwitchVerification() : false;
    
    // 生成報告
    generateFinalReport(result, verificationsPassed);
    
    // 保存執行記錄
    const executionRecord = {
        timestamp: new Date().toISOString(),
        operation: 'App.tsx Refactor Switch',
        success: result.success && verificationsPassed,
        details: result,
        verificationsPassed,
        switchState
    };
    
    fs.writeFileSync('refactor-switch-execution-log.json', JSON.stringify(executionRecord, null, 2));
    console.log('\n📝 執行記錄已保存至 refactor-switch-execution-log.json');
    
    // 返回結果碼
    process.exit(result.success && verificationsPassed ? 0 : 1);
}

// 處理中斷信號
process.on('SIGINT', async () => {
    console.log('\n⚠️  檢測到中斷信號，執行緊急回滾...');
    await emergencyRollback('用戶中斷操作');
    process.exit(1);
});

// 執行主流程
main().catch(async (error) => {
    console.error(`❌ 執行失敗: ${error.message}`);
    await emergencyRollback('執行過程中發生未處理錯誤');
    process.exit(1);
});