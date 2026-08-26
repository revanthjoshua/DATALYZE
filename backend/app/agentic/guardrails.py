class AgenticGuardrails:
    """
    FUTURE (Phase 5): Safety boundaries separating read-only analysis from active company modifications.
    """
    @staticmethod
    def is_action_permitted(action_type: str) -> bool:
        # Strictly read-only analysis in default mode
        return action_type in ["read_kpi", "run_detection", "run_prediction", "query_noah"]
