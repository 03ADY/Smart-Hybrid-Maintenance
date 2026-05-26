"""Train LSTM health model and save metadata for the model card."""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.models import Sequential

from maintenance.config import MODEL_META_PATH, MODEL_PATH
from maintenance.core import SupervisedConfig


def create_synthetic_data_for_training(config: SupervisedConfig, num_samples: int = 5000):
    time = np.linspace(0, 100, num_samples)
    features = [np.sin(time * 0.5)]
    for i in range(1, config.feature_dim):
        features.append(np.random.uniform(0, 1, num_samples) + np.sin(time * i * 0.1))
    features = np.column_stack(features).astype(np.float32)
    X, y = [], []
    for i in range(len(features) - config.sequence_length):
        X.append(features[i : i + config.sequence_length])
        y.append(features[i + config.sequence_length, 0])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def train_model():
    print("--- PredictiveOps Model Training ---")
    config = SupervisedConfig()
    X_train, y_train = create_synthetic_data_for_training(config)
    print(f"Data: X={X_train.shape}, y={y_train.shape}")

    model = Sequential([
        LSTM(50, activation="relu", input_shape=(config.sequence_length, config.feature_dim)),
        Dense(25, activation="relu"),
        Dense(1),
    ])
    model.compile(optimizer="adam", loss="mean_squared_error")

    history = model.fit(X_train, y_train, epochs=5, batch_size=64, verbose=1)
    final_loss = float(history.history["loss"][-1])

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(MODEL_PATH))
    MODEL_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_META_PATH.write_text(
        json.dumps({
            "trained": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "epochs": 5,
            "loss": round(final_loss, 6),
            "sequence_length": config.sequence_length,
            "feature_dim": config.feature_dim,
        }, indent=2),
        encoding="utf-8",
    )
    print(f"Saved {MODEL_PATH} and {MODEL_META_PATH}")


if __name__ == "__main__":
    train_model()
