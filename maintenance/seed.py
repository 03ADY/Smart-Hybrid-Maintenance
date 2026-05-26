"""Pre-seed SQLite with fleet scans for instant demos."""

import random

import database
from maintenance.config import MODEL_PATH, NUM_MACHINES
from maintenance.core import HybridMaintenanceSystem, SupervisedConfig, create_synthetic_data
from maintenance.scenarios import get_scenario


def seed_force(cycles: int = 12) -> int:
    """Always write fresh demo telemetry (after reset)."""
    if not MODEL_PATH.exists():
        return -1
    from tensorflow.keras.models import load_model

    model = load_model(str(MODEL_PATH))
    system = HybridMaintenanceSystem(model, get_scenario("Plant stress"))
    pool = create_synthetic_data(SupervisedConfig(), num_samples=300)
    written = 0
    for _ in range(cycles):
        for mid in range(NUM_MACHINES):
            idx = random.randint(0, len(pool) - 1)
            database.add_report(system.monitor_machine(mid, pool[idx]))
            written += 1
    return written


def seed_if_empty(min_rows: int = 80) -> int:
    database.init_db()
    with __import__("sqlite3").connect(database.DB_FILE) as conn:
        count = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    if count >= min_rows:
        return 0
    if not MODEL_PATH.exists():
        return -1

    from tensorflow.keras.models import load_model

    model = load_model(str(MODEL_PATH))
    system = HybridMaintenanceSystem(model, get_scenario("Plant stress"))
    pool = create_synthetic_data(SupervisedConfig(), num_samples=300)
    written = 0
    for _ in range(12):
        for mid in range(NUM_MACHINES):
            idx = random.randint(0, len(pool) - 1)
            report = system.monitor_machine(mid, pool[idx])
            database.add_report(report)
            written += 1
    return written
