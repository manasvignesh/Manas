"""Experimental India V1 distributions; these are synthetic, not census estimates."""

INDIA_V1 = {
    "metadata": {
        "name": "India V1",
        "version": "2026.1",
        "description": "Experimental synthetic population distribution; not statistically representative.",
        "sources": [],
    },
    "regions": [("South", 0.25), ("North", 0.25), ("West", 0.19), ("East", 0.18), ("Central", 0.08), ("Northeast", 0.05)],
    "urbanicity": [("urban", 0.48), ("semi-urban", 0.29), ("rural", 0.23)],
    "occupations": [("student", 0.22), ("salaried professional", 0.24), ("small business owner", 0.12), ("gig worker", 0.09), ("homemaker", 0.1), ("farmer", 0.07), ("service worker", 0.1), ("retired", 0.06)],
    "income_bands": [("low", 0.32), ("lower-middle", 0.29), ("middle", 0.25), ("upper-middle", 0.11), ("high", 0.03)],
}

LOCATIONS = {
    "South": [("Bengaluru", "Kannada"), ("Hyderabad", "Telugu"), ("Chennai", "Tamil"), ("Kochi", "Malayalam")],
    "North": [("Delhi", "Hindi"), ("Jaipur", "Hindi"), ("Lucknow", "Hindi"), ("Chandigarh", "Punjabi")],
    "West": [("Mumbai", "Marathi"), ("Pune", "Marathi"), ("Ahmedabad", "Gujarati"), ("Surat", "Gujarati")],
    "East": [("Kolkata", "Bengali"), ("Bhubaneswar", "Odia"), ("Patna", "Hindi"), ("Ranchi", "Hindi")],
    "Central": [("Bhopal", "Hindi"), ("Indore", "Hindi"), ("Raipur", "Hindi")],
    "Northeast": [("Guwahati", "Assamese"), ("Shillong", "English"), ("Imphal", "Manipuri")],
}

FIRST_NAMES = {
    "female": ["Aanya", "Diya", "Ishita", "Kavya", "Meera", "Nandini", "Priya", "Riya", "Saanvi", "Zoya"],
    "male": ["Aarav", "Arjun", "Dev", "Ishaan", "Kabir", "Manav", "Rahul", "Rohan", "Vihaan", "Yash"],
    "non-binary": ["Arya", "Kiran", "Noor", "Rishi", "Samar"],
}
LAST_NAMES = ["Sharma", "Patel", "Reddy", "Das", "Iyer", "Singh", "Khan", "Gupta", "Nair", "Joshi", "Bose", "Mehta"]
INTERESTS = ["fitness", "technology", "gaming", "personal finance", "fashion", "food", "travel", "music", "education", "entrepreneurship", "movies", "sustainability", "family", "cricket"]
VALUES = ["family", "independence", "security", "achievement", "tradition", "privacy", "community", "convenience", "health", "creativity"]
GOALS = ["improve health", "save money", "advance career", "support family", "learn new skills", "gain confidence", "start a business", "reduce stress"]
CONTRADICTIONS = [
    "Claims to save money but impulse-buys technology.",
    "Values privacy but rarely checks app permissions.",
    "Says advertising has no effect but follows influencers heavily.",
    "Rarely exercises but often buys fitness products.",
    "Prefers familiar brands but enjoys trying novel apps.",
    "Avoids subscriptions but forgets to cancel free trials.",
]

