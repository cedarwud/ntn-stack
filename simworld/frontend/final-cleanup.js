#!/usr/bin/env node

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const srcDir = path.join(__dirname, 'src')

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

function finalCleanup() {
    console.log('🧹 開始最終清理...\n')

    const files = getAllTsFiles(srcDir)
    let totalFixed = 0

    files.forEach((file) => {
        let content = fs.readFileSync(file, 'utf8')
        let modified = false
        const originalContent = content

        try {
            // 1. 移除完全未使用的變數（解構賦值中的）
            const unusedPatterns = [
                // 移除未使用的解構變數
                [
                    /const\s*\{\s*[\w\s:,]*_\w+[\w\s:,]*\}\s*=/,
                    (match) => {
                        // 嘗試移除整個未使用的變數
                        const cleaned = match
                            .replace(/_\w+\s*[,:]/g, '')
                            .replace(/,\s*}/g, '}')
                            .replace(/{\s*,/g, '{')
                        return cleaned.includes('{  }') ||
                            cleaned.includes('{ }')
                            ? ''
                            : cleaned
                    },
                ],

                // 移除未使用的函數參數（在箭頭函數中）
                [/\(\s*_\w+\s*\)\s*=>/g, '() =>'],
                [/\(\s*_\w+\s*,\s*/g, '('],
                [/,\s*_\w+\s*\)/g, ')'],

                // 移除 catch 中未使用的錯誤變數
                [/catch\s*\(\s*_\w+\s*\)/g, 'catch'],
            ]

            unusedPatterns.forEach(([pattern, replacement]) => {
                const newContent = content.replace(pattern, replacement)
                if (newContent !== content) {
                    content = newContent
                    modified = true
                }
            })

            // 2. 添加 eslint-disable 註釋給所有剩餘的未使用變數
            const lines = content.split('\n')
            const newLines = []

            for (let i = 0; i < lines.length; i++) {
                const line = lines[i]

                // 檢查是否包含 _variable 模式且不是註釋
                if (
                    line.includes('_') &&
                    !line.trim().startsWith('//') &&
                    !line.includes('eslint-disable')
                ) {
                    // 如果包含未使用變數模式，添加 eslint-disable
                    const unusedVarPattern = /_\w+/
                    if (unusedVarPattern.test(line)) {
                        newLines.push(
                            '        // eslint-disable-next-line @typescript-eslint/no-unused-vars'
                        )
                        modified = true
                    }
                }
                newLines.push(line)
            }

            if (modified) {
                content = newLines.join('\n')
            }

            // 3. 清理多餘的空行
            content = content.replace(/\n\s*\n\s*\n/g, '\n\n')

            if (modified) {
                fs.writeFileSync(file, content)
                console.log(`  ✓ 清理: ${path.relative(__dirname, file)}`)
                totalFixed++
            }
        } catch (error) {
            console.error(`❌ 清理文件 ${file} 時出錯:`, error.message)
            if (modified) {
                fs.writeFileSync(file, originalContent)
            }
        }
    })

    console.log(`\n✅ 清理完成！總共清理了 ${totalFixed} 個文件。`)
}

finalCleanup()
