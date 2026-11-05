import os
import json
import joblib
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    xgb = None
    HAS_XGBOOST = False
    from sklearn.ensemble import GradientBoostingClassifier
import numpy as np
from typing import Dict, List, Any, Tuple
from app.config import MODELS_DIR


FEATURE_NAMES = [
    "distance_from_ev",
    "vehicle_speed",
    "lane_position",
    "available_yielding_space",
    "time_since_announcement",
    "previous_yielding_actions",
    "speed_reduction",
    "lateral_movement",
    "response_time"
]


class CompliancePredictor:
    """
    XGBoost Classifier to predict driver yielding compliance to emergency vehicles.
    """
    def __init__(self):
        self.model_path = MODELS_DIR / "compliance_xgb.joblib"
        if HAS_XGBOOST:
            self.model = xgb.XGBClassifier(
                n_estimators=80,
                max_depth=4,
                learning_rate=0.08,
                objective="multi:softprob",
                num_class=3,  # 0: Low Compliance, 1: Medium Compliance, 2: High Compliance
                random_state=42,
                eval_metric="mlogloss"
            )
        else:
            self.model = GradientBoostingClassifier(
                n_estimators=80,
                max_depth=4,
                learning_rate=0.08,
                random_state=42
            )
        self.is_trained = False
        self.feature_importances: Dict[str, float] = {}
        self._load_or_train()

    def _load_or_train(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                self._compute_feature_importances()
                print("Loaded trained XGBoost Driver Compliance model from disk via joblib.")
                return
            except Exception as e:
                print(f"Failed to load XGBoost model via joblib: {e}. Retraining...")
        self.train_and_save()

    def train_and_save(self, n_samples: int = 1500):
        print("Training XGBoost Driver Compliance model...")
        np.random.seed(42)

        # 1. Generate realistic driver yielding training data
        # High compliance drivers: low response time, high available space, prior yielding history, speed reduction
        # Low compliance drivers: distracted/aggressive, low prior yielding, delayed response, high speed
        # Medium compliance: moderate delays, limited yielding space

        distances = np.random.uniform(20.0, 450.0, size=n_samples)
        speeds = np.random.uniform(20.0, 70.0, size=n_samples)
        lanes = np.random.choice([1, 2, 3], size=n_samples, p=[0.33, 0.34, 0.33])
        avail_spaces = np.random.uniform(10.0, 95.0, size=n_samples)
        announcement_times = np.random.uniform(1.0, 30.0, size=n_samples)
        prior_actions = np.random.randint(0, 12, size=n_samples)
        speed_reductions = np.random.uniform(-5.0, 25.0, size=n_samples)
        lateral_moves = np.random.uniform(0.0, 3.5, size=n_samples)
        response_times = np.random.uniform(1.0, 14.0, size=n_samples)

        X = np.column_stack([
            distances,
            speeds,
            lanes,
            avail_spaces,
            announcement_times,
            prior_actions,
            speed_reductions,
            lateral_moves,
            response_times
        ])

        # Ground truth rule-based labelling with stochastic noise
        # High yielding propensity score
        score = (
            (prior_actions / 11.0) * 0.30 +
            (avail_spaces / 100.0) * 0.25 +
            (speed_reductions / 25.0) * 0.20 +
            (lateral_moves / 3.5) * 0.15 -
            (response_times / 14.0) * 0.25 -
            (speeds / 70.0) * 0.10 +
            np.random.normal(0, 0.08, n_samples)
        )

        y = np.zeros(n_samples, dtype=int)
        y[score > 0.42] = 2  # High
        y[(score >= 0.20) & (score <= 0.42)] = 1  # Medium
        y[score < 0.20] = 0  # Low

        self.model.fit(X, y)
        self.is_trained = True
        self._compute_feature_importances()

        try:
            joblib.dump(self.model, self.model_path)
            print(f"XGBoost model trained and saved to {self.model_path} via joblib.")
        except Exception as e:
            print(f"Warning: could not save XGBoost model to disk: {e}")

    def _compute_feature_importances(self):
        try:
            importances = self.model.feature_importances_
            total = sum(importances) if sum(importances) > 0 else 1.0
            self.feature_importances = {
                name: round(float(imp / total), 4)
                for name, imp in zip(FEATURE_NAMES, importances)
            }
        except Exception:
            self.feature_importances = {name: round(1.0 / len(FEATURE_NAMES), 4) for name in FEATURE_NAMES}

    def predict_compliance(
        self,
        vehicle: Dict[str, Any],
        behaviour: Dict[str, Any],
        ev_distance: float,
        time_since_announcement: float = 6.0,
        available_space: float = 65.0
    ) -> Dict[str, Any]:
        """
        Executes actual XGBoost forward inference on vehicle and driver behaviour features.
        """
        vid = vehicle.get("vehicle_id")
        dist = max(5.0, ev_distance)
        speed = float(vehicle.get("speed", 40.0))
        lane = int(vehicle.get("current_lane", 2))
        prior_actions = int(behaviour.get("previous_yielding_actions", 4))
        resp_time = float(behaviour.get("response_time", 2.5))

        # Recent speed reduction from acceleration history
        accel_hist = behaviour.get("acceleration_history", [0.0])
        speed_red = -float(np.mean(accel_hist)) * 3.6  # convert to km/h reduction
        lateral_mv = 2.5 if "->" in str(behaviour.get("lane_change_history", "")) else 0.4

        features = np.array([[
            dist,
            speed,
            lane,
            available_space,
            time_since_announcement,
            prior_actions,
            speed_red,
            lateral_mv,
            resp_time
        ]])

        probs = self.model.predict_proba(features)[0]  # [P(Low), P(Med), P(High)]
        # Yielding probability is high-compliance prob + 0.5 * medium-compliance prob
        yielding_prob = round(float(probs[2] + 0.45 * probs[1]), 3)
        yielding_prob = max(0.05, min(0.99, yielding_prob))

        pred_class_idx = int(np.argmax(probs))
        class_map = {0: "Low", 1: "Medium", 2: "High"}
        compliance_class = class_map[pred_class_idx]
        confidence = round(float(probs[pred_class_idx]), 3)

        # Contribution factors for this specific prediction
        contributions = {
            "previous_yielding_record": round(prior_actions / 12.0, 2),
            "response_time_penalty": round(max(0.0, 1.0 - resp_time / 10.0), 2),
            "available_space_ratio": round(available_space / 100.0, 2),
            "speed_reduction_readiness": round(max(0.0, min(1.0, speed_red / 15.0)), 2)
        }

        return {
            "vehicle_id": vid,
            "yielding_probability": yielding_prob,
            "compliance_class": compliance_class,
            "compliance_confidence": confidence,
            "class_probabilities": {
                "low": round(float(probs[0]), 3),
                "medium": round(float(probs[1]), 3),
                "high": round(float(probs[2]), 3)
            },
            "contributing_features": contributions,
            "global_feature_importances": self.feature_importances,
            "raw_features": {
                "distance_from_ev": round(dist, 1),
                "vehicle_speed": speed,
                "lane_position": lane,
                "available_space": available_space,
                "previous_yielding_actions": prior_actions,
                "response_time": resp_time
            }
        }


compliance_predictor = CompliancePredictor()
