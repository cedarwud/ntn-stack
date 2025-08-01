# Phase 4: Docker 部署與系統整合

## 目標
優化現有 Docker 架構，整合 D2/A4/A5 事件處理，確保系統在 NTPU 場景下的穩定運行。

## Docker 架構優化

### 4.1 更新 Dockerfile 支援事件處理

```dockerfile
# netstack/docker/Dockerfile 修改
FROM python:3.10-slim as builder

# 第一階段：預處理
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製必要檔案
COPY tle_data/ ./tle_data/
COPY build_with_phase0_data.py .
COPY generate_d2a4a5_events.py .  # 新增事件生成腳本

# 執行預處理
RUN python build_with_phase0_data.py && \
    python generate_d2a4a5_events.py

# 第二階段：運行環境
FROM python:3.10-slim

WORKDIR /app
COPY --from=builder /build/data /app/data
COPY . .

# Volume 掛載點
VOLUME ["/app/data", "/app/tle_data"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 4.2 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  netstack-api:
    build:
      context: ./netstack
      dockerfile: docker/Dockerfile
    container_name: netstack-api
    ports:
      - "8080:8080"
    volumes:
      - netstack-data:/app/data
      - ./netstack/tle_data:/app/tle_data:ro
    environment:
      - SCENE_ID=ntpu
      - ENABLE_D2A4A5_EVENTS=true
      - EVENT_UPDATE_INTERVAL=30
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - netstack-network

  redis-cache:
    image: redis:7-alpine
    container_name: netstack-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    networks:
      - netstack-network

  simworld-backend:
    depends_on:
      netstack-api:
        condition: service_healthy
    volumes:
      - ./simworld/backend:/app
      - netstack-data:/app/netstack/data:ro  # 共享預計算資料
    environment:
      - NETSTACK_API_URL=http://netstack-api:8080
    networks:
      - netstack-network

volumes:
  netstack-data:
    driver: local
  redis-data:
    driver: local

networks:
  netstack-network:
    driver: bridge
```

### 4.3 事件生成腳本

```python
# generate_d2a4a5_events.py
#!/usr/bin/env python3
"""
生成 D2/A4/A5 事件資料
在 Docker build 階段執行
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class D2A4A5EventGenerator:
    def __init__(self, data_dir="/app/data"):
        self.data_dir = Path(data_dir)
        self.orbit_file = self.data_dir / "phase0_precomputed_orbits.json"
        self.events_dir = self.data_dir / "events"
        self.events_dir.mkdir(exist_ok=True)
        
        # 分層門檻
        self.thresholds = {
            'pre_handover': 13.5,
            'execution': 11.25,
            'critical': 5.0
        }
        
    def load_orbit_data(self):
        """載入預計算軌道資料"""
        with open(self.orbit_file, 'r') as f:
            return json.load(f)
            
    def generate_events(self):
        """生成換手事件"""
        orbit_data = self.load_orbit_data()
        events = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'scene': 'ntpu',
            'thresholds': self.thresholds,
            'd2_events': [],
            'a4_events': [],
            'a5_events': [],
            'timeline': []  # 時間軸事件序列
        }
        
        # 掃描所有衛星的可見性窗口
        for constellation in ['starlink', 'oneweb']:
            satellites = orbit_data['constellations'][constellation]['orbit_data']['satellites']
            
            for sat_id, sat_data in satellites.items():
                # 處理每個可見性窗口
                for window in sat_data['visibility_windows']:
                    # 檢測 D2 事件
                    if window['max_elevation'] < self.thresholds['critical'] + 2.0:
                        events['d2_events'].append({
                            'satellite_id': sat_id,
                            'window_start': window['start_time'],
                            'window_end': window['end_time'],
                            'max_elevation': window['max_elevation'],
                            'urgency': 'critical'
                        })
                    
                    # 檢測 A4 事件
                    if window['max_elevation'] > self.thresholds['execution']:
                        events['a4_events'].append({
                            'satellite_id': sat_id,
                            'window_start': window['start_time'],
                            'max_elevation': window['max_elevation'],
                            'duration': window['duration_seconds']
                        })
        
        # 儲存事件資料
        output_file = self.events_dir / "ntpu_handover_events.json"
        with open(output_file, 'w') as f:
            json.dump(events, f, indent=2)
            
        logger.info(f"生成事件統計:")
        logger.info(f"  D2 事件: {len(events['d2_events'])}")
        logger.info(f"  A4 事件: {len(events['a4_events'])}")
        logger.info(f"  A5 事件: {len(events['a5_events'])}")
        
if __name__ == "__main__":
    generator = D2A4A5EventGenerator()
    generator.generate_events()
```

### 4.4 健康檢查與監控

```python
# health_check.py
from fastapi import FastAPI
from datetime import datetime
import json
from pathlib import Path

app = FastAPI()

@app.get("/health")
async def health_check():
    """系統健康檢查"""
    data_dir = Path("/app/data")
    
    checks = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # 檢查軌道資料
    orbit_file = data_dir / "phase0_precomputed_orbits.json"
    if orbit_file.exists():
        checks["components"]["orbit_data"] = {
            "status": "ok",
            "size_mb": orbit_file.stat().st_size / 1024 / 1024
        }
    else:
        checks["components"]["orbit_data"] = {"status": "missing"}
        checks["status"] = "degraded"
    
    # 檢查事件資料
    event_file = data_dir / "events" / "ntpu_handover_events.json"
    if event_file.exists():
        with open(event_file, 'r') as f:
            event_data = json.load(f)
        checks["components"]["event_data"] = {
            "status": "ok",
            "d2_events": len(event_data.get('d2_events', [])),
            "a4_events": len(event_data.get('a4_events', [])),
            "generated_at": event_data.get('generated_at')
        }
    else:
        checks["components"]["event_data"] = {"status": "missing"}
    
    return checks
```

### 4.5 Volume 管理策略

```bash
#!/bin/bash
# manage_volumes.sh

# 建立必要的 volume
docker volume create netstack-data
docker volume create netstack-tle-data

# 更新 TLE 資料的腳本
update_tle_data() {
    echo "更新 TLE 資料..."
    
    # 下載最新 TLE (實際實現需要 API key)
    # curl -o new_tle.zip https://example.com/tle/latest
    
    # 解壓到臨時目錄
    # unzip new_tle.zip -d /tmp/new_tle
    
    # 複製到 volume
    docker run --rm \
        -v netstack-tle-data:/data \
        -v /tmp/new_tle:/source \
        alpine cp -r /source/* /data/
        
    echo "TLE 資料更新完成"
}

# 重新生成預計算資料
regenerate_data() {
    echo "重新生成預計算資料..."
    
    docker run --rm \
        -v netstack-tle-data:/app/tle_data:ro \
        -v netstack-data:/app/data \
        netstack-builder \
        bash -c "python build_with_phase0_data.py && python generate_d2a4a5_events.py"
        
    echo "預計算資料生成完成"
}

# 備份資料
backup_data() {
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="/backup/netstack/${timestamp}"
    
    mkdir -p ${backup_dir}
    
    # 備份 volume
    docker run --rm \
        -v netstack-data:/data:ro \
        -v ${backup_dir}:/backup \
        alpine tar czf /backup/netstack-data.tar.gz -C /data .
        
    echo "備份完成: ${backup_dir}"
}
```

### 4.6 環境變數配置

```env
# .env.production
# NetStack 配置
SCENE_ID=ntpu
MIN_ELEVATION=10.0
PRE_HANDOVER_THRESHOLD=13.5
EXECUTION_THRESHOLD=11.25
CRITICAL_THRESHOLD=5.0

# Redis 快取
REDIS_HOST=netstack-redis
REDIS_PORT=6379
REDIS_DB=0
CACHE_TTL=300

# 效能調校
WORKER_THREADS=4
MAX_CONNECTIONS=1000
REQUEST_TIMEOUT=30

# 監控
ENABLE_METRICS=true
METRICS_PORT=9090
LOG_LEVEL=INFO
```

## 預期成果

- **建構時間**：< 5 分鐘（含預處理）
- **映像檔大小**：< 500MB
- **啟動時間**：< 30 秒
- **記憶體使用**：< 2GB
- **Volume 備份**：自動化每日備份