"""Hardcoded scripted consultations for the CivicConnect demo."""

CONSULTATIONS = {
    "mobility_porto": {
        "id": "mobility_porto",
        "title": "Porto Sustainable Mobility Plan 2030",
        "level": "Municipal",
        "level_emoji": "🏛️",
        "entity": "City of Porto",
        "summary": (
            "The City of Porto proposes converting 12 km of central car lanes into "
            "protected cycling and pedestrian paths, with 3 new electric bus corridors. "
            "The plan aims to reduce car traffic in the historical centre by 40% and "
            "cut transport-related CO₂ emissions by 25% by 2030."
        ),
        "detail": (
            "Key measures:\n"
            "• 12 km of protected cycling lanes across Bonfim, Cedofeita, and Massarelos\n"
            "• 3 electric bus corridors with 10-minute frequency\n"
            "• 500 new e-bike sharing stations\n"
            "• Car-free zone in Ribeira district (daily 10:00–18:00)\n"
            "• 2,400 new public parking spaces in park-and-ride facilities\n\n"
            "Estimated investment: €120M over 4 years. Partially funded by EU Urban Mobility grants."
        ),
        "deadline": "15 July 2026",
        "status": "open",
        "result": None,
    },
    "digital_id_pt": {
        "id": "digital_id_pt",
        "title": "Digital Public Services Mandate",
        "level": "National",
        "level_emoji": "🇵🇹",
        "entity": "Portuguese Government",
        "summary": (
            "Portugal's government proposes making Chave Móvel Digital the mandatory "
            "authentication method for all public online services, replacing physical ID "
            "for digital interactions. The measure would affect 8.5 million citizens and "
            "is expected to save €180M annually in administrative costs."
        ),
        "detail": (
            "What changes:\n"
            "• All public services (Finance, Health, Social Security) require CMD login\n"
            "• Physical ID cards remain valid for in-person interactions\n"
            "• Free CMD setup at any public service counter or Post Office\n"
            "• 3-year transition period for those without smartphones\n"
            "• Dedicated support line for digital inclusion\n\n"
            "Critics raise concerns about digital exclusion of elderly citizens and "
            "those in rural areas with poor connectivity."
        ),
        "deadline": "1 August 2026",
        "status": "open",
        "result": None,
    },
}

EU_RESULT = {
    "id": "eu_renovation",
    "title": "EU Green Deal: Building Renovation Wave — Results",
    "level": "European Union",
    "level_emoji": "🇪🇺",
    "entity": "European Commission",
    "summary": (
        "The European Commission gathered citizen input on mandatory energy efficiency "
        "standards for buildings. Over 2.3 million responses were received across 27 member states."
    ),
    "result": (
        "📊 Final results:\n"
        "• 68% supported mandatory renovation targets for buildings\n"
        "• 74% requested financial support for low-income households\n"
        "• 61% backed phased implementation (5-year window)\n\n"
        "🏛️ Commission response:\n"
        "The European Commission committed to a phased approach requiring "
        "all residential buildings to reach energy class D by 2033, with a €72B "
        "dedicated renovation fund and priority access for households below the median income threshold.\n\n"
        "The directive enters into force Q1 2027."
    ),
    "status": "closed",
    "deadline": "Closed — March 2026",
}
