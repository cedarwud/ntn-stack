#!/usr/bin/env node

/**
 * 前端測試快速執行器
 * 
 * 提供簡單的命令行接口來執行不同類型的前端測試
 * 
 * 使用方法:
 *   node test-runner.js [command]
 * 
 * 命令:
 *   all        執行所有測試 (默認)
 *   components 執行組件測試
 *   api        執行 API 測試
 *   e2e        執行 E2E 測試
 *   console    執行 Console 錯誤檢測
 *   watch      監視模式
 *   coverage   生成覆蓋率報告
 */

const { spawn } = require('child_process')
const path = require('path')

// 顏色定義
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
}

function log(message, color = colors.white) {
  console.log(`${color}${message}${colors.reset}`)
}

function logInfo(message) {
  log(`[INFO] ${message}`, colors.blue)
}

function logSuccess(message) {
  log(`[SUCCESS] ${message}`, colors.green)
}

function logError(message) {
  log(`[ERROR] ${message}`, colors.red)
}

function logWarning(message) {
  log(`[WARNING] ${message}`, colors.yellow)
}

function printBanner() {
  log('\n╔══════════════════════════════════════════════════════════════╗', colors.cyan)
  log('║                  NTN-Stack 前端測試執行器                   ║', colors.cyan)
  log('║                                                              ║', colors.cyan)
  log('║  🧪 快速執行前端測試，驗證重構後的功能是否正常             ║', colors.cyan)
  log('╚══════════════════════════════════════════════════════════════╝', colors.cyan)
  log('')
}

function printHelp() {
  printBanner()
  log('使用方法: node test-runner.js [command]')
  log('')
  log('命令:')
  log('  all        執行所有測試 (默認)')
  log('  components 執行組件測試')
  log('  api        執行 API 測試')
  log('  e2e        執行 E2E 測試')
  log('  console    執行 Console 錯誤檢測')
  log('  watch      監視模式')
  log('  coverage   生成覆蓋率報告')
  log('  help       顯示此幫助信息')
  log('')
  log('範例:')
  log('  node test-runner.js            # 執行所有測試')
  log('  node test-runner.js components # 只執行組件測試')
  log('  node test-runner.js watch      # 監視模式')
}

function runVitest(args, options = {}) {
  return new Promise((resolve, reject) => {
    logInfo(`執行命令: npm run test ${args.join(' ')}`)
    
    const child = spawn('npm', ['run', 'test', '--', ...args], {
      stdio: 'inherit',
      cwd: process.cwd(),
      ...options
    })
    
    child.on('close', (code) => {
      if (code === 0) {
        logSuccess('測試執行完成')
        resolve(code)
      } else {
        logError(`測試失敗，退出碼: ${code}`)
        reject(new Error(`Test failed with exit code ${code}`))
      }
    })
    
    child.on('error', (error) => {
      logError(`執行測試時發生錯誤: ${error.message}`)
      reject(error)
    })
  })
}

async function runTests(command) {
  printBanner()
  
  try {
    switch (command) {
      case 'all':
      case undefined:
        logInfo('執行所有前端測試...')
        await runVitest(['--run'])
        break
        
      case 'components':
        logInfo('執行組件測試...')
        await runVitest(['--run', 'src/test/components.test.tsx'])
        break
        
      case 'api':
        logInfo('執行 API 測試...')
        await runVitest(['--run', 'src/test/api.test.ts'])
        break
        
      case 'e2e':
        logInfo('執行 E2E 測試...')
        await runVitest(['--run', 'src/test/e2e.test.tsx'])
        break
        
      case 'console':
        logInfo('執行 Console 錯誤檢測...')
        await runVitest(['--run', 'src/test/console-errors.test.ts'])
        break
        
      case 'watch':
        logInfo('啟動監視模式...')
        await runVitest(['--watch'])
        break
        
      case 'coverage':
        logInfo('生成覆蓋率報告...')
        await runVitest(['--coverage'])
        break
        
      case 'help':
        printHelp()
        return
        
      default:
        logError(`未知命令: ${command}`)
        printHelp()
        process.exit(1)
    }
    
    logSuccess('🎉 測試執行成功！')
    
  } catch (error) {
    logError('💥 測試執行失敗！')
    process.exit(1)
  }
}

// 主執行邏輯
const command = process.argv[2]

// 檢查是否在正確的目錄
const packageJsonPath = path.join(process.cwd(), 'package.json')
try {
  require(packageJsonPath)
} catch (error) {
  logError('請在前端項目根目錄執行此腳本 (需要 package.json)')
  process.exit(1)
}

// 檢查測試文件是否存在
const testFiles = [
  'src/test/setup.ts',
  'src/test/components.test.tsx',
  'src/test/api.test.ts',
  'src/test/e2e.test.tsx',
  'src/test/console-errors.test.ts'
]

let missingFiles = []
testFiles.forEach(file => {
  const filePath = path.join(process.cwd(), file)
  try {
    require.resolve(filePath)
  } catch (error) {
    missingFiles.push(file)
  }
})

if (missingFiles.length > 0) {
  logWarning('以下測試文件不存在:')
  missingFiles.forEach(file => {
    logWarning(`  - ${file}`)
  })
  logWarning('部分測試可能無法執行')
}

// 執行測試
runTests(command)