from pathlib import Path

APP_NAME = "PredictiveOps Enterprise"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "health_model.h5"
MODEL_META_PATH = PROJECT_ROOT / "models" / "model_meta.json"

NUM_MACHINES = 10
FAULTY_MACHINES = [2, 5, 7, 9]

HEALTH_CRITICAL = 0.5
HEALTH_WARNING = 0.75

# Demo economics ($)
DEFAULT_DOWNTIME_COST_PER_HOUR = 5_000
DEFAULT_PREVENTIVE_COST = 2_500
DEFAULT_REPLACE_COST = 45_000
HOURS_SAVED_EARLY_ACTION = 8

FEATURE_NAMES = [
    "vibration", "temperature", "pressure", "current", "voltage",
    "rpm", "oil_level", "humidity", "acoustic", "magnetic_field",
]

ACTION_LABELS = {0: "No action", 1: "Inspect", 2: "Major service", 3: "Replace unit"}

FAULT_SCENARIOS = [
    {"problem": "Critical overheating", "resolution": "Inspect cooling system; reduce load immediately.", "priority": "P1"},
    {"problem": "Excessive vibration", "resolution": "Check bearings and alignment; schedule vibration analysis.", "priority": "P2"},
    {"problem": "Pressure drop", "resolution": "Inspect hydraulics for leaks; verify pump pressure.", "priority": "P2"},
    {"problem": "Voltage instability", "resolution": "Verify power supply connections and grounding.", "priority": "P1"},
]

PLAYBOOKS = {
    "Critical overheating": "Dispatch technician within 2h · Reduce load 40% · Log thermal trend",
    "Excessive vibration": "Schedule bearing inspection · Compare RMS vs baseline · Plan outage window",
    "Pressure drop": "Hydraulic line check · Seal replacement kit on standby",
    "Voltage instability": "Electrical panel inspection · UPS failover test",
}
