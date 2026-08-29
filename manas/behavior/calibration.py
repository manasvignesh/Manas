from dataclasses import dataclass


@dataclass(frozen=True)
class BehaviorCalibration:
    """Named behavioral strengths for reproducible, inspectable tuning."""

    target_relevance_weight: float = .38
    category_interest_weight: float = .27
    life_context_weight: float = .24
    price_sensitivity_strength: float = .30
    price_decision_strength: float = 3.50
    social_influence_strength: float = .28
    privacy_base_strength: float = .42
    privacy_event_strength: float = .34
    habit_strength: float = .48
    memory_decay_half_life_days: float = 10.0
    minimum_segment_size: int = 5
    minimum_segment_fraction: float = .05


DEFAULT_CALIBRATION = BehaviorCalibration()
