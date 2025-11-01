from abc import ABC, abstractmethod
from typing import Dict, Any

class IJudgeModel(ABC):
    model_id: str

    @abstractmethod
    def judge(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Return dict with fields: {"latency_ms": float, "json": str, "provider_raw": dict}"""
        ...
