請針對這個專案的整體，提供一份詳細完整的 README.md，不需要特別強調軍事用途，不要參考現有專案的文件描述，不用提供學習資源、中長期目標等，也不需要提供 api 介面或使用範例、部署專案等，也不要系統需求或進度，不要使用表格，完全只針對現有的專案已完成的現況，尤其是 navbar 及 sidebar 中所有已完成的項目，做一份完整詳細的說明，目的是為了評估專案的現況，來決定後續要再開發的方向

> 目前 skyfield 衛星 tle 的相關邏輯，是獨立出來的嗎?是否有跟其他程式有耦合性過高的問題?
  請提供測試程式並直接幫我執行驗證，確認都有達到以上說的部份

● 我需要檢查 skyfield TLE 相關邏輯的獨立性和耦合性問題，並創建測試程式進行驗證。

● Task(Search TLE related files)
  ⎿  Done (30 tool uses · 61.0k tokens · 3m 11.6s)

● 現在讓我檢查具體的 TLE 相關檔案來分析耦合性：

● Read(simworld/backend/app/domains/satellite/services/tle_service.py)
  ⎿  Read 471 lines (ctrl+r to expand)

● Read(simworld/backend/app/domains/satellite/interfaces/tle_service_interface.py)
  ⎿  Read 41 lines (ctrl+r to expand)

● Search(pattern: "TLEService|tle_service", include: "*.py")
  ⎿  Found 7 files (ctrl+r to expand)

● 現在讓我創建一個全面的測試程式來驗證 TLE 服務的獨立性和耦合性：

● Write(test_tle_independence.py)
  ⎿  Wrote 582 lines to test_tle_independence.py
     #!/usr/bin/env python3
     """
     TLE服務獨立性和耦合性測試程式
     測試 skyfield TLE 相關邏輯的模組化程度和依賴關係
     """
     import asyncio
     import sys
     import os
     import json
     … +572 lines (ctrl+r to expand)

● Bash(python test_tle_independence.py)
  ⎿  🚀 開始TLE服務獨立性和耦合性測試...
     ============================================================

     📋 運行: test_tle_service_imports
     … +60 lines (ctrl+r to expand)

● 我發現問題：TLE服務由於導入依賴導致無法獨立測試。讓我檢查依賴關係並創建一個獨立的測試
  版本：

● Bash(cd /home/sat/ntn-stack/simworld/backend && pip install sqlmodel aiohttp sgp4
      skyfield)
  ⎿  Collecting sqlmodel
       Using cached sqlmodel-0.0.24-py3-none-any.whl.metadata (10 kB)
     Requirement already satisfied: aiohttp in
     /home/sat/ntn-stack/venv/lib/python3.11/site-packages (3.12.6)
     Requirement already satisfied: sgp4 in
     /home/sat/ntn-stack/venv/lib/python3.11/site-packages (2.24)
     … +28 lines (ctrl+r to expand)

● Bash(cd /home/sat/ntn-stack && python test_tle_independence.py)
  ⎿  🚀 開始TLE服務獨立性和耦合性測試...
     ============================================================

     📋 運行: test_tle_service_imports
     … +74 lines (ctrl+r to expand)

● 問題在於數據庫依賴。讓我創建一個針對耦合性問題的獨立測試程式：

● Write(isolated_tle_test.py)
  ⎿  Wrote 661 lines to isolated_tle_test.py
     #!/usr/bin/env python3
     """
     TLE服務獨立性測試 - 隔離版本
     創建獨立的TLE服務版本來測試耦合性問題
     """
     import asyncio
     import sys
     import os
     import json
     … +651 lines (ctrl+r to expand)