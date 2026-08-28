"""Rule and ontology based scenario parsing with no model dependency."""

from __future__ import annotations

import re
import shlex

from manas.simulation.models import ProductScenario


CATEGORIES = {
    "fitness": {"fitness", "workout", "exercise", "gym", "diet", "health coach", "calorie"},
    "education": {"study", "student", "exam", "learning", "course", "tutor", "college"},
    "finance": {"finance", "budget", "invest", "saving", "money", "banking", "loan"},
    "productivity": {"productivity", "planner", "task", "calendar", "focus", "habit"},
    "commerce": {"shopping", "marketplace", "delivery", "store", "retail"},
    "mobility": {"transport", "transit", "ride", "commute", "vehicle"},
    "entertainment": {"game", "gaming", "music", "movie", "streaming", "social app"},
}

BENEFITS = {
    "personalization": {"personalized", "personalised", "personalization", "custom", "tailored", "coach"},
    "convenience": {"easy", "instant", "convenient", "automate", "automatic", "on demand"},
    "lower cost": {"affordable", "cheap", "save money", "lower cost", "discount"},
    "accountability": {"accountability", "consistent", "motivate", "habit", "reminder"},
    "speed": {"fast", "faster", "quick", "time-saving"},
}

COMPETITORS = {
    "fitness": ["free workout content", "personal trainers", "other fitness apps"],
    "education": ["free videos", "teachers and tutors", "other learning apps"],
    "finance": ["spreadsheets", "banking apps", "financial advisers"],
    "productivity": ["paper planning", "calendar apps", "other task managers"],
    "general": ["free alternatives", "existing habits", "doing nothing"],
}


def sanitize_idea(value: str) -> str:
    """Extract the idea if a user accidentally pastes an entire MANAS command."""
    text = value.strip()
    if not re.search(r"(?:^|\s)(?:python\s+-m\s+)?manas(?:\.exe)?\s+simulate\b", text, re.I):
        return text
    try:
        tokens = shlex.split(text, posix=False)
    except ValueError:
        tokens = text.split()
    if "--idea" in tokens:
        index = tokens.index("--idea") + 1
        parts = []
        while index < len(tokens) and not tokens[index].startswith("--"):
            parts.append(tokens[index].strip("\"'"))
            index += 1
        if parts:
            return " ".join(parts).strip()
    return ""


def _matches(text: str, ontology: dict[str, set[str]]) -> list[str]:
    return [label for label, terms in ontology.items() if any(term in text for term in terms)]


def _price(text: str) -> float | None:
    patterns = [r"₹\s*([\d,]+(?:\.\d+)?)", r"\b(?:inr|rs\.?)\s*([\d,]+(?:\.\d+)?)", r"\bat\s+([\d,]+(?:\.\d+)?)\s*(?:/\s*month|monthly)"]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def parse_scenario(
    idea: str,
    *,
    price: float | None = None,
    pricing_model: str | None = None,
    target_audience: str | None = None,
    description: str | None = None,
) -> ProductScenario:
    cleaned = sanitize_idea(idea)
    if not cleaned:
        raise ValueError("Enter an idea, not a MANAS shell command without an --idea value.")
    text = cleaned.casefold()
    categories = _matches(text, CATEGORIES)
    primary = categories[0] if categories else "general"
    parsed_price = _price(cleaned)
    model = "monthly" if re.search(r"monthly|/\s*month|subscription", text) else "annual" if re.search(r"annual|yearly|/\s*year", text) else "free" if "free" in text else "one-time"
    technologies = [name for name, terms in {"AI": {"ai", "artificial intelligence"}, "mobile app": {"app", "mobile"}, "software": {"software", "platform", "app"}}.items() if any(re.search(rf"\b{re.escape(term)}\b", text) for term in terms)]
    if "AI" in technologies and "software" not in technologies:
        technologies.append("software")
    audience = target_audience or ("college students" if any(term in text for term in ("college student", "university student", "students")) else "general consumers")
    benefits = _matches(text, BENEFITS)
    privacy = .75 if any(term in text for term in ("health", "fitness", "location", "camera", "voice", "personal data")) and technologies else .2 if technologies else .08
    effort = .75 if primary in {"fitness", "education", "productivity"} else .35
    novelty = .72 if "AI" in technologies else .45 if technologies else .25
    concerns = []
    if (price if price is not None else parsed_price or 0) > 0:
        concerns.append("price")
    if privacy >= .5:
        concerns.append("privacy")
    return ProductScenario(
        name=cleaned,
        description=description or cleaned,
        target_audience=audience,
        price=max(0, price if price is not None else parsed_price or 0),
        pricing_model=pricing_model or model,
        category=primary,
        secondary_categories=categories[1:],
        technologies=technologies,
        benefits=benefits or (["personalization"] if "AI" in technologies else []),
        competitors=COMPETITORS.get(primary, COMPETITORS["general"]),
        behavior_change_required=effort,
        privacy_exposure=privacy,
        novelty=novelty,
        concerns=concerns,
        raw_input=idea,
    )
