"""Load LSTM when available; numpy fallback for Streamlit Cloud (no TensorFlow)."""

from pathlib import Path

import numpy as np

from maintenance.config import MODEL_PATH


class NumpyHealthPredictor:
    """Lightweight stand-in for LSTM — same predict() shape, no TensorFlow."""

    def predict(self, sensor_data: np.ndarray, verbose: int = 0) -> np.ndarray:
        if len(sensor_data.shape) == 2:
            sensor_data = sensor_data[np.newaxis, ...]
        window = sensor_data[0]
        baseline = float(np.mean(window[:, 0]))
        mse = float(np.mean((window[:, 0] - baseline) ** 2))
        return np.array([[mse]], dtype=np.float32)


def load_health_model(path: Path | None = None):
    path = path or MODEL_PATH
    if path.exists():
        try:
            from tensorflow.keras.models import load_model
            return load_model(str(path))
        except Exception:
            pass
    return NumpyHealthPredictor()
