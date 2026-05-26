"""Predictive maintenance core: LSTM health + policy + sensor explainability."""

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from maintenance.analytics import detect_sensor_anomalies
from maintenance.config import (
    ACTION_LABELS,
    FAULT_SCENARIOS,
    FAULTY_MACHINES,
    FEATURE_NAMES,
    HEALTH_CRITICAL,
    HEALTH_WARNING,
)


@dataclass
class SupervisedConfig:
    sequence_length: int = 100
    feature_dim: int = 10


def create_synthetic_data(config: SupervisedConfig, num_samples: int = 1000) -> np.ndarray:
    time = np.linspace(0, 10, num_samples)
    features = [np.sin(time * 0.5)]
    for i in range(1, config.feature_dim):
        features.append(np.random.uniform(0, 1, num_samples) + np.sin(time * i * 0.1))
    features = np.column_stack(features).astype(np.float32)
    return np.array(
        [features[i : i + config.sequence_length] for i in range(len(features) - config.sequence_length)],
        dtype=np.float32,
    )


def _latest_sensor_vector(sensor_data: np.ndarray) -> np.ndarray:
    if len(sensor_data.shape) == 3:
        return sensor_data[0, -1, :]
    if len(sensor_data.shape) == 2:
        return sensor_data[-1, :]
    return sensor_data


def _explanation_from_sensors(vector: np.ndarray) -> dict[str, float]:
    baseline = np.full(len(vector), 0.5)
    imp = np.abs(vector - baseline)
    if imp.sum() == 0:
        imp = np.ones_like(imp)
    imp = imp / imp.sum()
    return dict(zip(FEATURE_NAMES, (imp / imp.sum()).tolist()))


def _status_label(score: float) -> str:
    if score < HEALTH_CRITICAL:
        return "CRITICAL"
    if score < HEALTH_WARNING:
        return "WARNING"
    return "HEALTHY"


class HybridMaintenanceSystem:
    def __init__(self, model, scenario: dict | None = None):
        self.health_model = model
        self.scenario = scenario or {}
        self.metrics: dict[str, list] = {"health_predictions": [], "explanations": []}

    def set_scenario(self, scenario: dict) -> None:
        self.scenario = scenario

    def predict_health(self, sensor_data: np.ndarray) -> dict[str, Any]:
        if len(sensor_data.shape) == 2:
            sensor_data = sensor_data[np.newaxis, ...]
        val = float(self.health_model.predict(sensor_data, verbose=0)[0][0])
        score = 1 / (1 + max(0, val))
        return {
            "health_score": score,
            "failure_prob": 1 - score,
            "rul": score * 100,
            "status": _status_label(score),
        }

    def monitor_machine(self, machine_id: int, sensor_data: np.ndarray) -> dict[str, Any]:
        health = self.predict_health(sensor_data)
        sensors = _latest_sensor_vector(sensor_data)
        sensor_map = dict(zip(FEATURE_NAMES, sensors.tolist()))
        explanation = _explanation_from_sensors(sensors)

        problem, resolution, priority = "No issue detected.", "Continue standard operation.", "—"
        mult = float(self.scenario.get("fault_multiplier", 1.0))
        force_only = self.scenario.get("force_faulty_only", False)
        base_prob = 0.25 * mult
        is_faulty_machine = machine_id in FAULTY_MACHINES
        trigger = (is_faulty_machine or not force_only) and random.random() < base_prob

        target = self.scenario.get("target_machine")
        if target is not None and machine_id == target:
            trigger = True

        if trigger and (is_faulty_machine or not force_only):
            health["health_score"] = random.uniform(0.2, 0.5)
            health["failure_prob"] = 1 - health["health_score"]
            health["rul"] = health["health_score"] * 100
            health["status"] = _status_label(health["health_score"])
            forced = self.scenario.get("forced_problem")
            if forced:
                fault = next(f for f in FAULT_SCENARIOS if f["problem"] == forced)
            else:
                fault = random.choice(FAULT_SCENARIOS)
            problem = fault["problem"]
            resolution = fault["resolution"]
            priority = fault.get("priority", "P2")

        score = health["health_score"]
        if score < HEALTH_CRITICAL:
            action = 3
        elif score < HEALTH_WARNING:
            action = 2
        elif problem != "No issue detected.":
            action = 1
        else:
            action = 0

        sensor_alerts = detect_sensor_anomalies(sensor_map)
        report = {
            "machine_id": machine_id,
            "timestamp": datetime.utcnow().isoformat(),
            "health_metrics": health,
            "maintenance_action": {"action": action, "label": ACTION_LABELS.get(action, "?")},
            "explanation": explanation,
            "sensor_snapshot": sensor_map,
            "sensor_alerts": sensor_alerts,
            "problem_description": problem,
            "suggested_resolution": resolution,
            "priority": priority,
            "work_order": {
                "title": f"M{machine_id:02d} — {problem}" if problem != "No issue detected." else f"M{machine_id:02d} — Routine OK",
                "priority": priority,
                "eta_hours": 2 if action >= 2 else 24 if action == 1 else 0,
                "status": "OPEN" if action > 0 else "CLOSED",
            },
        }
        self.metrics["health_predictions"].append(health)
        return report

    def monitor_fleet(self, machine_ids: list[int], data_pool: np.ndarray) -> dict[int, dict]:
        reports = {}
        for mid in machine_ids:
            idx = random.randint(0, len(data_pool) - 1)
            reports[mid] = self.monitor_machine(mid, data_pool[idx])
        return reports

    def health_trend_df(self, limit: int = 80) -> pd.DataFrame:
        return pd.DataFrame(self.metrics["health_predictions"][-limit:])
