from __future__ import annotations

import random
from typing import TypeVar

from manas.agents.models import Agent, CategoryExperience, DynamicState, LifeContext, Personality, ProductOpinion
from manas.population.distributions import CONTRADICTIONS, FIRST_NAMES, GOALS, INTERESTS, LAST_NAMES, LIFE_CONTEXTS, LOCATIONS, VALUES
from manas.population.loader import load_pack
from manas.utils.random import clamp, seeded

T = TypeVar("T")


def weighted(rng: random.Random, choices: list[tuple[T, float]]) -> T:
    return rng.choices([x[0] for x in choices], weights=[x[1] for x in choices], k=1)[0]


class PopulationGenerator:
    def __init__(self, seed: int, pack: str = "india_v1") -> None:
        self.rng = seeded(seed, "population")
        self.pack = load_pack(pack)

    def generate(self, size: int = 100) -> list[Agent]:
        return [self._agent(index) for index in range(size)]

    def _score(self, mean: float = 0.5, spread: float = 0.2) -> float:
        return clamp(self.rng.gauss(mean, spread))

    def _agent(self, index: int) -> Agent:
        gender = weighted(self.rng, [("female", .48), ("male", .49), ("non-binary", .03)])
        region = weighted(self.rng, self.pack["regions"])
        city, local_language = self.rng.choice(LOCATIONS[region])
        urbanicity = weighted(self.rng, self.pack["urbanicity"])
        occupation = weighted(self.rng, self.pack["occupations"])
        income_band = weighted(self.rng, self.pack["income_bands"])
        age = int(self.rng.triangular(18, 72, 29))
        if occupation == "student":
            age = self.rng.randint(17, 27)
        elif occupation == "retired":
            age = self.rng.randint(58, 78)
        disposable_ranges = {"low": (500, 4500), "lower-middle": (2500, 9000), "middle": (7000, 22000), "upper-middle": (18000, 55000), "high": (45000, 160000)}
        low, high = disposable_ranges[income_band]
        disposable = round(self.rng.uniform(low, high), -1)
        education = self.rng.choice(["secondary", "undergraduate", "graduate", "vocational", "postgraduate"])
        tech_mean = 0.68 if age < 35 or occupation in {"student", "salaried professional"} else 0.42
        technology = self._score(tech_mean, .17)
        internet = clamp(technology * .72 + self._score(.6, .2) * .28)
        frugality = self._score(.58 if income_band in {"low", "lower-middle"} else .45)
        personality = Personality(
            curiosity=self._score(), impulsiveness=self._score(.43), skepticism=self._score(.52),
            risk_tolerance=self._score(.45), social_conformity=self._score(.55),
            novelty_seeking=self._score(.5), frugality=frugality,
        )
        count = self.rng.choices([0, 1, 2, 3], weights=[.18, .46, .27, .09], k=1)[0]
        interests = self.rng.sample(INTERESTS, k=self.rng.randint(2, 5))
        values = self.rng.sample(VALUES, k=self.rng.randint(2, 4))
        context_pool = list(LIFE_CONTEXTS)
        if occupation == "student":
            context_pool += [item for item in LIFE_CONTEXTS if item[0] in {"exam preparation", "starting college", "fitness push"}] * 2
        contexts = []
        for situation, description, themes, urgency, financial_effect in self.rng.sample(context_pool, k=self.rng.choice([1, 1, 2])):
            contexts.append(LifeContext(situation=situation, description=description, themes=themes,
                urgency=clamp(urgency + self.rng.uniform(-.12, .12)), financial_effect=clamp(financial_effect + self.rng.uniform(-.1, .1), -1, 1),
                remaining_days=self.rng.randint(14, 120)))
        experience_categories = set(self.rng.sample(["fitness", "education", "finance", "productivity", "entertainment", "technology"], k=3))
        category_experiences = {}
        for category in sorted(experience_categories):
            familiarity = self._score(.65 if category in interests else .35, .18)
            used, satisfaction = max(0, int(self.rng.gauss(familiarity * 4, 1.2))), self._score(.5, .24)
            notes = ["Tried several options and was disappointed."] if used >= 2 and satisfaction < .4 else ["Had a useful experience in this category."] if satisfaction > .68 else []
            if personality.frugality > .65:
                notes.append("Usually compares free alternatives first.")
            category_experiences[category] = CategoryExperience(category=category, products_used=used,
                paid_before=used > 0 and self.rng.random() < clamp(.2 + (1 - frugality) * .55), satisfaction=satisfaction,
                familiarity=familiarity, notes=notes)
        return Agent(
            id=f"agent_{index + 1:04d}", name=f"{self.rng.choice(FIRST_NAMES[gender])} {self.rng.choice(LAST_NAMES)}",
            age=age, gender=gender, location=city, region=region, urbanicity=urbanicity,
            occupation=occupation, education=education, languages=list(dict.fromkeys([local_language, "Hindi", "English"] if technology > .55 else [local_language, "Hindi"])),
            household=self.rng.choice(["nuclear family", "joint family", "shared accommodation", "living alone", "couple"]),
            income_band=income_band, disposable_income=disposable, technology_familiarity=technology,
            internet_usage=internet, interests=interests, goals=self.rng.sample(GOALS, k=2), values=values,
            beliefs=[self.rng.choice(["quality is worth paying for", "free alternatives are usually enough", "recommendations from friends matter", "brands must earn trust"])],
            personality=personality,
            state=DynamicState(mood=self._score(), motivation=self._score(), financial_pressure=clamp(frugality + self.rng.uniform(-.2, .2)), current_interest=self._score(.3),
                attention=self._score(.58), curiosity=clamp(personality.curiosity * .6 + self._score(.5) * .4),
                stress=self._score(.42), skepticism=clamp(personality.skepticism * .7 + self._score(.5) * .3), fatigue=self._score(.2, .12)),
            privacy_sensitivity=self._score(.55), price_sensitivity=clamp(frugality * .65 + self._score(.5) * .35),
            brand_sensitivity=self._score(.45), status_seeking=self._score(.4), habit_strength=self._score(.55), trust_tendency=self._score(.5),
            contradictions=self.rng.sample(CONTRADICTIONS, k=count), previous_experiences=self.rng.sample(["used a disappointing subscription", "found value in a free trial", "bought after a friend's recommendation", "ignored an influencer promotion", "returned an expensive purchase"], k=self.rng.randint(0, 2)),
            life_contexts=contexts, category_experiences=category_experiences,
            opinion=ProductOpinion(interest=self._score(.2, .1), trust=self._score(.25, .1), price_acceptance=clamp(1 - frugality, .05, .9)),
        )
