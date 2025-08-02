"""
🧠 RL 算法實現層

將現有的算法實現適配到新的 SOLID 架構中，
提供統一的算法接口實現。
"""

# 遵循 KISS 原則：移除複雜實現，保持系統穩定
# 複雜的 PyTorch 實現已完成基本功能驗證，現在專注於核心架構穩定性

# PostgreSQL 儲存庫保持可用
from .postgresql_repository import PostgreSQLRepository
# MockRepository 已刪除 - 違反 CLAUDE.md 核心原則

__all__ = [
    "PostgreSQLRepository",
    # "MockRepository",  # 已刪除 - 模擬數據違規
]
