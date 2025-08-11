// 定義衛星通過軌跡數據 - 基於新竹地區(24.7867°N, 120.9969°E)可能觀察到的OneWeb衛星通過軌跡
// OneWeb衛星軌道傾角約87.9°，主要是近極地軌道

export interface SatellitePassTemplate {
    startAzimuth: number;
    endAzimuth: number;
    maxElevation: number;
    name: string;
}

export const satellitePassTemplates: SatellitePassTemplate[] = [
    // 主要從南到北或北到南的通過 (符合極軌道衛星特性)
    {
        startAzimuth: 170,
        endAzimuth: 350,
        maxElevation: 85,
        name: '高仰角極軌道(南到北)',
    },
    {
        startAzimuth: 350,
        endAzimuth: 170,
        maxElevation: 80,
        name: '高仰角極軌道(北到南)',
    },

    // 低仰角的南北通過
    {
        startAzimuth: 160,
        endAzimuth: 340,
        maxElevation: 30,
        name: '低仰角極軌道(南到北)',
    },
    {
        startAzimuth: 340,
        endAzimuth: 160,
        maxElevation: 25,
        name: '低仰角極軌道(北到南)',
    },

    // 由於在新竹(24.78°N)，稍偏東西的通過也會出現
    {
        startAzimuth: 135,
        endAzimuth: 315,
        maxElevation: 65,
        name: '東南到西北通過',
    },
    {
        startAzimuth: 45,
        endAzimuth: 225,
        maxElevation: 60,
        name: '東北到西南通過',
    },

    // 較罕見的東西通過 (由於軌道傾角87.9°，在24.78°N緯度會有部分偏東西的通過)
    {
        startAzimuth: 105,
        endAzimuth: 255,
        maxElevation: 40,
        name: '偏東到偏西通過',
    },
    {
        startAzimuth: 75,
        endAzimuth: 285,
        maxElevation: 35,
        name: '偏東到偏西通過',
    },
]; 