"""Demo scenarios for presenter-controlled fault rates."""

SCENARIOS: dict[str, dict] = {
    "Normal operations": {
        "fault_multiplier": 0.4,
        "force_faulty_only": False,
        "blurb": "Low alert rate — stable plant narrative.",
    },
    "Plant stress": {
        "fault_multiplier": 1.8,
        "force_faulty_only": True,
        "blurb": "Elevated risk on assets 2, 5, 7, 9.",
    },
    "Cooling failure drill": {
        "fault_multiplier": 2.5,
        "force_faulty_only": True,
        "forced_problem": "Critical overheating",
        "target_machine": 5,
        "blurb": "Machine #5 overheating — executive drill.",
    },
    "Custom": {
        "fault_multiplier": 1.0,
        "force_faulty_only": False,
        "blurb": "Use sidebar thresholds and machine picker.",
    },
}


def get_scenario(name: str) -> dict:
    return SCENARIOS.get(name, SCENARIOS["Normal operations"]).copy()
