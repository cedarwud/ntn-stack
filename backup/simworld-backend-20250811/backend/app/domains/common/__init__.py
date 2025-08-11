"""
共享領域模組

包含所有領域共用的模型、接口和工具。
"""

# 從基本模型導出
from app.domains.common.models.base_model import (
    DomainBaseModel,
    Entity,
    AuditableEntity,
    ValueObject,
)

# 從結果工具導出
from app.domains.common.utils.result import (
    Result,
    ResultStatus,
    Error,
)

# 從儲存庫接口導出
from app.domains.common.interfaces.repository_interface import (
    RepositoryInterface,
)

# 從值對象導出
from app.domains.common.value_objects.coordinate import (
    Coordinate,
)
