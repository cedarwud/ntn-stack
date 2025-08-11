from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict, TypeVar, Generic
import uuid


class DomainBaseModel(BaseModel):
    """所有領域模型的基類"""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        validate_assignment=True,
    )


class Entity(DomainBaseModel):
    """實體基類，具有唯一標識符"""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="實體唯一識別符"
    )


class AuditableEntity(Entity):
    """可審計實體，包含創建和修改時間戳"""

    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="創建時間"
    )
    updated_at: Optional[datetime] = Field(None, description="最後更新時間")
    created_by: Optional[str] = Field(None, description="創建者")
    updated_by: Optional[str] = Field(None, description="最後更新者")


class ValueObject(DomainBaseModel):
    """值對象基類，通常是不可變的且通過其屬性值來定義相等性"""

    pass
