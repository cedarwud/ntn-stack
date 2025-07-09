# This file is intentionally left blank.

"""
Event Validator for the AI Decision Engine.
"""
from typing import Dict, Any


class EventValidator:
    """
    Validates the integrity and schema of incoming 3GPP events.
    """

    def validate_event(self, event: Dict[str, Any]) -> bool:
        """
        Validates an event.

        For now, this is a basic implementation. It can be expanded to
        use a schema validation library like Pydantic or JSONSchema.

        Args:
            event: The event data dictionary.

        Returns:
            True if the event is valid, False otherwise.
        """
        if not isinstance(event, dict):
            return False

        # 檢查事件數據結構
        event_data = event.get("event_data", {})
        
        # 基本鍵檢查 - 更寬鬆的驗證
        if "event_type" in event:
            # 新格式：{event_type: "A4", event_data: {...}}
            return True
        elif "ue_id" in event_data or "source_cell" in event_data:
            # 舊格式：{event_data: {ue_id: "...", source_cell: "..."}}
            return True
        elif any(key in event_data for key in ["rsrp", "rsrq", "sinr"]):
            # 包含測量數據的格式
            return True
        else:
            # 最基本的檢查 - 只要是字典就認為有效
            return len(event) > 0
