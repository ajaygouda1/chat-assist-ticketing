import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

class FraudDetector:
    """
    Isolation Forest Anomaly Detection for Booking & Payment Behavior.
    Features: [booking_velocity_24h, failed_payment_ratio, distinct_ips, seconds_between_actions]
    """
    def __init__(self):
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.is_fitted = False
        self._fit_default()

    def _fit_default(self):
        # Normal booking behavior sample dataset
        normal_behavior = np.array([
            [1, 0.0, 1, 120],
            [2, 0.0, 1, 300],
            [3, 0.1, 1, 450],
            [1, 0.0, 2, 60],
            [2, 0.2, 1, 180],
            [4, 0.0, 1, 90],
            [1, 0.0, 1, 600],
            [2, 0.0, 1, 400],
        ])
        self.model.fit(normal_behavior)
        self.is_fitted = True

    def analyze_transaction(self, velocity: int, failed_ratio: float, distinct_ips: int, time_delta: float) -> dict:
        if not self.is_fitted:
            self._fit_default()

        record = np.array([[velocity, failed_ratio, distinct_ips, time_delta]])
        prediction = self.model.predict(record)[0]  # -1 for anomaly, 1 for normal
        score = float(self.model.decision_function(record)[0])

        is_suspicious = bool(prediction == -1 or velocity > 5 or failed_ratio > 0.4 or distinct_ips > 3)
        reason = "High velocity and rapid multi-IP bookings detected" if is_suspicious else "Normal pattern"

        return {
            "is_suspicious": is_suspicious,
            "anomaly_score": round(-score, 3),
            "reason": reason,
            "metrics": {
                "velocity": velocity,
                "failed_ratio": failed_ratio,
                "distinct_ips": distinct_ips,
                "time_delta": time_delta
            }
        }

fraud_detector = FraudDetector()
