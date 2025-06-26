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

function handleUnusedVariables() {
    console.log('🧹 處理未使用變數...\n')

    const files = getAllTsFiles(srcDir)
    let totalFixed = 0

    files.forEach((file) => {
        let content = fs.readFileSync(file, 'utf8')
        let modified = false
        const originalContent = content

        try {
            // 1. 處理完全未使用的 useState 變數
            content = content.replace(
                /const\s+\[\s*([_\w]+),\s*([_\w]+)\s*\]\s*=\s*useState/g,
                (match, getter, setter) => {
                    // 檢查是否在代碼中使用
                    const getterUsed = content
                        .split('\n')
                        .some(
                            (line) =>
                                line.includes(getter) &&
                                !line.includes('useState') &&
                                !line.includes('=')
                        )
                    const setterUsed = content
                        .split('\n')
                        .some(
                            (line) =>
                                line.includes(setter) &&
                                !line.includes('useState')
                        )

                    if (!getterUsed && !setterUsed) {
                        modified = true
                        return `const [_${getter}, _${setter}] = useState`
                    } else if (!getterUsed) {
                        modified = true
                        return `const [_${getter}, ${setter}] = useState`
                    } else if (!setterUsed) {
                        modified = true
                        return `const [${getter}, _${setter}] = useState`
                    }
                    return match
                }
            )

            // 2. 處理解構賦值中的未使用變數
            content = content.replace(
                /const\s*\{\s*([^}]+)\s*\}\s*=/g,
                (match, destructured) => {
                    const items = destructured
                        .split(',')
                        .map((item) => item.trim())
                    const newItems = items.map((item) => {
                        // 處理重命名的情況 (key: newName)
                        if (item.includes(':')) {
                            const [key, newName] = item
                                .split(':')
                                .map((s) => s.trim())
                            const varName = newName

                            // 檢查變數是否被使用
                            const isUsed = content
                                .split('\n')
                                .some(
                                    (line) =>
                                        line.includes(varName) &&
                                        !line.includes('const {') &&
                                        !line.includes('=')
                                )

                            if (!isUsed && !varName.startsWith('_')) {
                                modified = true
                                return `${key}: _${varName}`
                            }
                        } else {
                            // 簡單的解構
                            const varName = item
                            const isUsed = content
                                .split('\n')
                                .some(
                                    (line) =>
                                        line.includes(varName) &&
                                        !line.includes('const {') &&
                                        !line.includes('=')
                                )

                            if (!isUsed && !varName.startsWith('_')) {
                                modified = true
                                return `_${varName}`
                            }
                        }
                        return item
                    })

                    if (modified) {
                        return `const { ${newItems.join(', ')} } =`
                    }
                    return match
                }
            )

            // 3. 處理函數參數中的未使用變數
            content = content.replace(
                /\(\s*([^)]+)\s*\)\s*=>/g,
                (match, params) => {
                    const paramList = params.split(',').map((p) => p.trim())
                    const newParams = paramList.map((param) => {
                        // 簡單參數名提取
                        const paramName = param.split(':')[0].trim()

                        // 檢查是否使用
                        const isUsed = content
                            .split('\n')
                            .some(
                                (line) =>
                                    line.includes(paramName) &&
                                    !line.includes('=>') &&
                                    !line.includes('=')
                            )

                        if (!isUsed && !paramName.startsWith('_')) {
                            modified = true
                            return param.replace(paramName, `_${paramName}`)
                        }
                        return param
                    })

                    if (modified) {
                        return `(${newParams.join(', ')}) =>`
                    }
                    return match
                }
            )

            // 4. 移除完全未使用的變數聲明
            const lines = content.split('\n')
            const newLines = []

            for (let i = 0; i < lines.length; i++) {
                const line = lines[i]

                // 檢查是否為變數聲明且完全未使用
                const varDeclMatch = line.match(/^\s*const\s+(\w+)\s*=/)
                if (varDeclMatch) {
                    const varName = varDeclMatch[1]
                    const isUsed = lines.some(
                        (l, idx) => idx !== i && l.includes(varName)
                    )

                    if (!isUsed && !varName.startsWith('_')) {
                        // 跳過這一行（移除變數聲明）
                        modified = true
                        continue
                    }
                }

                newLines.push(line)
            }

            if (modified) {
                content = newLines.join('\n')
            }

            if (modified) {
                fs.writeFileSync(file, content)
                console.log(`  ✓ 處理: ${path.relative(__dirname, file)}`)
                totalFixed++
            }
        } catch (error) {
            console.error(`❌ 處理文件 ${file} 時出錯:`, error.message)
            if (modified) {
                fs.writeFileSync(file, originalContent)
            }
        }
    })

    console.log(`\n✅ 處理完成！總共處理了 ${totalFixed} 個文件。`)
}

handleUnusedVariables()
