from __future__ import annotations

from manas.agents.models import Agent
from manas.simulation.models import ProductScenario, TargetAudience


def parse_target_audience(text: str, category: str) -> TargetAudience:
    normalized = text.casefold()
    occupations = []
    education = []
    life_stages = []
    age_range = None
    if any(term in normalized for term in ("college student", "university student", "undergraduate")):
        occupations.append("student")
        education.extend(["undergraduate", "secondary"])
        life_stages.extend(["starting college", "college"])
        age_range = (17, 27)
    elif "student" in normalized:
        occupations.append("student")
        education.extend(["secondary", "undergraduate", "graduate"])
        age_range = (16, 30)
    occupation_terms = {
        "teacher": "teacher", "farmer": "farmer", "retired": "retired",
        "professional": "salaried professional", "small business": "small business owner",
    }
    for phrase, occupation in occupation_terms.items():
        if phrase in normalized and occupation not in occupations:
            occupations.append(occupation)
    regions = ["India"] if "india" in normalized or "indian" in normalized else []
    interests = [category] if category != "general" else []
    technology = .48 if any(term in normalized for term in ("ai", "app", "software", "digital")) else None
    return TargetAudience(
        age_range=age_range,
        occupations=occupations,
        education_states=education,
        regions=regions,
        interests=interests,
        life_stages=life_stages,
        minimum_technology_familiarity=technology,
    )


def target_match(agent: Agent, scenario: ProductScenario) -> float:
    target = scenario.target_profile
    components: list[tuple[float, float]] = []
    if target.occupations:
        components.append((.32, float(agent.occupation in target.occupations)))
    if target.age_range:
        low, high = target.age_range
        if low <= agent.age <= high:
            age_score = 1.0
        else:
            distance = min(abs(agent.age - low), abs(agent.age - high))
            age_score = max(0, 1 - distance / 18)
        components.append((.14, age_score))
    if target.education_states:
        components.append((.10, float(agent.education in target.education_states)))
    if target.regions:
        # India V1 agents are explicitly generated inside India.
        components.append((.05, float("India" in target.regions)))
    if target.interests:
        personal_themes = {item.casefold() for item in [*agent.interests, *agent.goals]}
        personal_themes.update(theme.casefold() for context in agent.life_contexts for theme in context.themes)
        score = max((float(any(interest in theme for theme in personal_themes)) for interest in target.interests), default=0)
        components.append((.22, score))
    if target.life_stages:
        situations = " ".join(context.situation.casefold() for context in agent.life_contexts)
        stage_score = float(agent.occupation == "student" or any(stage in situations for stage in target.life_stages))
        components.append((.10, stage_score))
    if target.minimum_technology_familiarity is not None:
        threshold = target.minimum_technology_familiarity
        components.append((.07, min(1, agent.technology_familiarity / max(threshold, .01))))
    if not components:
        return 0
    # Weights are absolute evidence, not normalized across whatever fields happen
    # to be present. A lone "uses technology" hint must not look like a full match.
    return sum(weight * score for weight, score in components)
