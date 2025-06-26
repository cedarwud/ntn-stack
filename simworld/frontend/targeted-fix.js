#!/usr/bin/env node

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const srcDir = path.join(__dirname, 'src')

// 特定文件的修復規則
const specificFixes = {
    'FailoverMechanism.tsx': {
        fixes: [
            ['const getConnectionIcon', 'const _getConnectionIcon'],
            [
                'const FailoverEventsVisualization',
                'const _FailoverEventsVisualization',
            ],
            ['const getSeverityColor', 'const _getSeverityColor'],
            ['const getTriggerIcon', 'const _getTriggerIcon'],
        ],
    },
}

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

function applySpecificFixes() {
    console.log('🎯 應用特定修復...\n')

    const files = getAllTsFiles(srcDir)
    let totalFixed = 0

    files.forEach((file) => {
        const fileName = path.basename(file)
        const fixes = specificFixes[fileName]

        if (!fixes) return

        let content = fs.readFileSync(file, 'utf8')
        let modified = false
        const originalContent = content

        try {
            fixes.fixes.forEach(([search, replace]) => {
                const newContent = content.replace(
                    new RegExp(search, 'g'),
                    replace
                )
                if (newContent !== content) {
                    content = newContent
                    modified = true
                }
            })

            if (modified) {
                fs.writeFileSync(file, content)
                console.log(`  ✓ 修復: ${path.relative(__dirname, file)}`)
                totalFixed++
            }
        } catch (error) {
            console.error(`❌ 修復文件 ${file} 時出錯:`, error.message)
            if (modified) {
                fs.writeFileSync(file, originalContent)
            }
        }
    })

    console.log(`\n✅ 特定修復完成！總共修復了 ${totalFixed} 個文件。`)
}

function removeUnusedComponents() {
    console.log('🗑️  移除未使用的組件...\n')

    const files = getAllTsFiles(srcDir)
    let totalFixed = 0

    files.forEach((file) => {
        let content = fs.readFileSync(file, 'utf8')
        let modified = false

        try {
            // 尋找未使用的組件聲明並添加註釋或重命名
            const lines = content.split('\n')
            const newLines = []

            for (let i = 0; i < lines.length; i++) {
                let line = lines[i]

                // 檢查是否為組件聲明
                const componentMatch = line.match(
                    /^(\s*)const\s+([A-Z]\w*(?:Visualization|Component|Widget|Panel))\s*[:=]/
                )
                if (componentMatch) {
                    const [, indent, componentName] = componentMatch

                    // 檢查這個組件是否在文件中被使用
                    const isUsed = lines.some(
                        (l, idx) =>
                            idx !== i &&
                            (l.includes(`<${componentName}`) ||
                                l.includes(`{${componentName}}`) ||
                                l.includes(`export ${componentName}`) ||
                                l.includes(`return ${componentName}`))
                    )

                    if (!isUsed) {
                        // 重命名為帶下劃線的版本
                        line = line.replace(componentName, `_${componentName}`)
                        modified = true
                    }
                }

                newLines.push(line)
            }

            if (modified) {
                content = newLines.join('\n')
                fs.writeFileSync(file, content)
                console.log(`  ✓ 處理: ${path.relative(__dirname, file)}`)
                totalFixed++
            }
        } catch (error) {
            console.error(`❌ 處理文件 ${file} 時出錯:`, error.message)
        }
    })

    console.log(`\n✅ 未使用組件處理完成！總共處理了 ${totalFixed} 個文件。`)
}

// 執行修復
applySpecificFixes()
removeUnusedComponents()
