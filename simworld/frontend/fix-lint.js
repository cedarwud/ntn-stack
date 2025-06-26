#!/usr/bin/env node

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const srcDir = path.join(__dirname, 'src')

// 修復特定的 lint 錯誤
function fixSpecificErrors() {
    console.log('🔧 開始修復特定的 lint 錯誤...\n')

    const files = getAllTsFiles(srcDir)

    files.forEach((file) => {
        let content = fs.readFileSync(file, 'utf8')
        let modified = false
        const originalContent = content

        try {
            // 1. 修復常見的 any 類型
            const anyReplacements = [
                [/\bevent:\s*any\b/g, 'event: Event'],
                [/\be:\s*any\b/g, 'e: Event'],
                [/\bdata:\s*any\b/g, 'data: unknown'],
                [/\bresponse:\s*any\b/g, 'response: unknown'],
                [/\bresult:\s*any\b/g, 'result: unknown'],
                [/\bvalue:\s*any\b/g, 'value: unknown'],
                [/\bitem:\s*any\b/g, 'item: unknown'],
                [/\bconfig:\s*any\b/g, 'config: Record<string, unknown>'],
                [/\boptions:\s*any\b/g, 'options: Record<string, unknown>'],
                [/\bparams:\s*any\b/g, 'params: Record<string, unknown>'],
                [/\bprops:\s*any\b/g, 'props: Record<string, unknown>'],
                [/\(...args:\s*any\[\]/g, '(...args: unknown[]'],
            ]

            anyReplacements.forEach(([pattern, replacement]) => {
                const newContent = content.replace(pattern, replacement)
                if (newContent !== content) {
                    content = newContent
                    modified = true
                }
            })

            // 2. 修復空介面
            content = content.replace(
                /interface\s+(\w+)\s*\{\s*\}/g,
                (match, interfaceName) => {
                    modified = true
                    return `type ${interfaceName} = Record<string, never>`
                }
            )

            // 3. 修復未使用的變數 - 添加下劃線前綴（簡單版本）
            content = content.replace(
                /\b(\w+):\s*([^,)]+)([,)])/g,
                (match, varName, type, ending) => {
                    // 基於常見的未使用變數名模式
                    if (
                        ['index', 'prev', 'e', 'error', 'event', '_'].includes(
                            varName
                        ) &&
                        content.includes('never used')
                    ) {
                        modified = true
                        return `_${varName}: ${type}${ending}`
                    }
                    return match
                }
            )

            // 4. 修復未使用的導入 useRef
            if (
                content.includes('useRef') &&
                content.includes('is defined but never used')
            ) {
                content = content.replace(
                    /import\s+React,\s*\{\s*([^}]*,\s*)?useRef(\s*,[^}]*)?\s*\}/g,
                    (match, before, after) => {
                        const parts = []
                        if (before) parts.push(before.replace(/,\s*$/, ''))
                        if (after) parts.push(after.replace(/^\s*,/, ''))

                        if (parts.length === 0) {
                            return 'import React'
                        } else {
                            return `import React, { ${parts.join(', ')} }`
                        }
                    }
                )
                modified = true
            }

            if (modified) {
                fs.writeFileSync(file, content)
                console.log(`  ✓ 修復: ${path.relative(__dirname, file)}`)
            }
        } catch (error) {
            console.error(`❌ 修復文件 ${file} 時出錯:`, error.message)
            // 如果修復失敗，恢復原始內容
            if (modified) {
                fs.writeFileSync(file, originalContent)
            }
        }
    })

    console.log('\n✅ 特定錯誤修復完成！')
}

// 獲取所有 TypeScript 文件
function getAllTsFiles(dir) {
    const files = []

    function traverse(currentDir) {
        try {
            const items = fs.readdirSync(currentDir)

            for (const item of items) {
                const fullPath = path.join(currentDir, item)
                const stat = fs.statSync(fullPath)

                if (
                    stat.isDirectory() &&
                    !item.startsWith('.') &&
                    item !== 'node_modules'
                ) {
                    traverse(fullPath)
                } else if (
                    stat.isFile() &&
                    (item.endsWith('.ts') || item.endsWith('.tsx'))
                ) {
                    files.push(fullPath)
                }
            }
        } catch (error) {
            console.error(`無法讀取目錄 ${currentDir}:`, error.message)
        }
    }

    traverse(dir)
    return files
}

// 執行修復
fixSpecificErrors()
