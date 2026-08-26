from typing import Dict, Any, Callable

class ToolRegistry:
    """
    FUTURE (Phase 5): Registers callable analytical tools for the autonomous planner.
    """
    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable):
        self._tools[name] = func

    def get_tool(self, name: str) -> Any:
        return self._tools.get(name)
