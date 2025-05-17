export function generateDeviceName(role: string, currentDevices: { name: string }[]): string {
    const prefix =
        role === 'desired'
            ? 'tx'
            : role === 'receiver'
            ? 'rx'
            : 'jam'
    const typeDevices = currentDevices.filter((d) => d.name.startsWith(prefix))
    let maxNum = 0
    typeDevices.forEach((device) => {
        const numPart = device.name.replace(prefix, '')
        const num = parseInt(numPart, 10)
        if (!isNaN(num) && num > maxNum) {
            maxNum = num
        }
    })
    return `${prefix}${maxNum + 1}`
} 