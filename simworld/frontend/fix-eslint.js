#!/usr/bin/env node

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

// Function to recursively find all TypeScript and JavaScript files
function findFiles(dir, extensions = ['.ts', '.tsx', '.js', '.jsx']) {
    let results = []
    const list = fs.readdirSync(dir)

    list.forEach((file) => {
        const filePath = path.join(dir, file)
        const stat = fs.statSync(filePath)

        if (stat && stat.isDirectory()) {
            // Skip node_modules and .git directories
            if (!['node_modules', '.git', 'dist', 'build'].includes(file)) {
                results = results.concat(findFiles(filePath, extensions))
            }
        } else {
            if (extensions.some((ext) => file.endsWith(ext))) {
                results.push(filePath)
            }
        }
    })

    return results
}

// Function to remove unused eslint-disable comments
function removeUnusedEslintDisables(filePath) {
    try {
        let content = fs.readFileSync(filePath, 'utf8')
        let modified = false

        // Remove unused eslint-disable directives
        const unusedDisablePattern =
            /^(\s*)\/\/\s*eslint-disable-next-line\s+@typescript-eslint\/no-unused-vars\s*$/gm
        const newContent = content.replace(
            unusedDisablePattern,
            (match, indent) => {
                // Check if the next line actually has unused vars
                const lines = content.split('\n')
                const matchIndex =
                    content.substring(0, content.indexOf(match)).split('\n')
                        .length - 1
                const nextLine = lines[matchIndex + 1]

                // If next line doesn't look like it needs the disable, remove it
                if (
                    !nextLine ||
                    (!nextLine.includes('=') &&
                        !nextLine.includes('const') &&
                        !nextLine.includes('let') &&
                        !nextLine.includes('var'))
                ) {
                    modified = true
                    return ''
                }
                return match
            }
        )

        if (modified) {
            fs.writeFileSync(filePath, newContent)
            console.log(`Fixed: ${filePath}`)
        }
    } catch (error) {
        console.error(`Error processing ${filePath}:`, error.message)
    }
}

// Main execution
const sourceDir = path.join(__dirname, 'src')
const files = findFiles(sourceDir)

console.log(`Found ${files.length} files to process...`)

files.forEach((file) => {
    removeUnusedEslintDisables(file)
})

console.log('Cleanup completed!')
