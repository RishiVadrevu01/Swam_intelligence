import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, List, Any, Tuple


class VehicleAnomalyDetector:
    """
    Isolation Forest anomaly detection on vehicle dynamics:
    - Speed (km/h)
    - Acceleration (m/s^2)
    - Delta Position (meters)
    - Heading Variation (deg)
    - Message Frequency (Hz)
    - Movement Consistency (0-1)
    """
    def __init__(self, contamination: float = 0.12, random_state: int = 42):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )
        self.is_trained = False
        self._fit_baseline_distribution()

    def _generate_synthetic_baseline(self, n_samples: int = 1200) -> np.ndarray:
        """
        Generates normal urban driving dynamics baseline plus a few anomalies for training.
        """
        np.random.seed(42)
        # Normal samples (approx 88%)
        n_normal = int(n_samples * 0.88)
        normal_speed = np.random.normal(loc=42.0, scale=8.0, size=n_normal)
        normal_speed = np.clip(normal_speed, 10.0, 65.0)

        normal_accel = np.random.normal(loc=0.0, scale=1.2, size=n_normal)
        normal_accel = np.clip(normal_accel, -3.5, 3.5)

        normal_delta_pos = np.random.normal(loc=12.0, scale=3.0, size=n_normal)
        normal_delta_pos = np.clip(normal_delta_pos, 2.0, 22.0)

        normal_heading_var = np.random.normal(loc=2.0, scale=1.5, size=n_normal)
        normal_heading_var = np.clip(normal_heading_var, 0.0, 10.0)

        normal_freq = np.random.normal(loc=10.0, scale=1.0, size=n_normal)  # 10 Hz V2X beacons
        normal_freq = np.clip(normal_freq, 6.0, 12.0)

        normal_mov_consist = np.random.uniform(0.80, 0.99, size=n_normal)

        normal_data = np.column_stack([
            normal_speed,
            normal_accel,
            normal_delta_pos,
            normal_heading_var,
            normal_freq,
            normal_mov_consist
        ])

        # Anomalous samples (approx 12%)
        n_anomaly = n_samples - n_normal
        # Unrealistic speeds (e.g. 130 km/h or sudden 0 km/h teleports)
        anomaly_speed = np.random.choice([110.0, 140.0, 0.5, 160.0], size=n_anomaly) + np.random.normal(0, 5, n_anomaly)
        # Sudden impossible accelerations
        anomaly_accel = np.random.choice([-8.5, 8.0, 9.5], size=n_anomaly)
        # Teleport jumps in position
        anomaly_delta_pos = np.random.uniform(45.0, 120.0, size=n_anomaly)
        # Random erratic heading swings
        anomaly_heading_var = np.random.uniform(35.0, 90.0, size=n_anomaly)
        # Irregular or spoofed message burst rates
        anomaly_freq = np.random.choice([0.5, 1.2, 45.0], size=n_anomaly)
        # Inconsistent movement trajectory
        anomaly_mov_consist = np.random.uniform(0.10, 0.40, size=n_anomaly)

        anomaly_data = np.column_stack([
            anomaly_speed,
            anomaly_accel,
            anomaly_delta_pos,
            anomaly_heading_var,
            anomaly_freq,
            anomaly_mov_consist
        ])

        return np.vstack([normal_data, anomaly_data])

    def _fit_baseline_distribution(self):
        baseline_X = self._generate_synthetic_baseline()
        self.model.fit(baseline_X)
        self.is_trained = True

    def extract_features(self, vehicle: Dict[str, Any], trust_info: Dict[str, Any]) -> List[float]:
        speed = float(vehicle.get("speed", 40.0))
        accel = float(vehicle.get("acceleration", 0.0))
        # Estimate delta position over last time step (meters)
        delta_pos = (speed / 3.6) * 1.0  # 1 second step
        heading_var = abs(float(vehicle.get("heading", 48.0)) - 48.0)
        freq = 10.0 * float(trust_info.get("message_freshness", 0.95))
        mov_consist = float(trust_info.get("movement_consistency", 0.90))

        return [speed, accel, delta_pos, heading_var, freq, mov_consist]

    def detect_anomaly(self, vehicle: Dict[str, Any], trust_info: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        features = np.array([self.extract_features(vehicle, trust_info)])
        # prediction: 1 = normal, -1 = anomaly
        pred = self.model.predict(features)[0]
        # anomaly score: negative indicates anomaly
        score = float(self.model.decision_function(features)[0])
        is_anomaly = bool(pred == -1)

        reasons = []
        speed = features[0][0]
        accel = features[0][1]
        delta_pos = features[0][2]
        heading_var = features[0][3]
        freq = features[0][4]
        mov_consist = features[0][5]

        if speed > 75.0:
            reasons.append(f"Unrealistic urban arterial speed ({speed:.1f} km/h > 75 km/h limit)")
        elif speed < 8.0 and not vehicle.get("is_stopped", False):
            reasons.append(f"Abnormally sluggish or stalling telemetry ({speed:.1f} km/h)")

        if abs(accel) > 4.5:
            reasons.append(f"Physically implausible acceleration/deceleration ({accel:.2f} m/s²)")

        if delta_pos > 30.0:
            reasons.append(f"Abrupt spatial teleport detected ({delta_pos:.1f}m in 1s)")

        if heading_var > 20.0:
            reasons.append(f"Suspicious angular trajectory deviation ({heading_var:.1f}°)")

        if freq < 3.0:
            reasons.append(f"Degraded V2X broadcast rate ({freq:.1f} Hz, stale beacon)")

        if mov_consist < 0.60:
            reasons.append(f"Trajectory kinematics inconsistent with road geometry (consistency: {mov_consist:.2f})")

        return is_anomaly, score, reasons


anomaly_detector = VehicleAnomalyDetector()
