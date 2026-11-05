from typing import Dict, List, Any
from app.config import TRUST_WEIGHTS, TRUST_THRESHOLDS
from app.core.anomaly_detector import anomaly_detector


class TrustEngine:
    """
    Behavioural Trust Evaluation Model:
    T(i) = w1*P(i) + w2*C(i) + w3*F(i) + w4*S(i)
    coupled with Isolation Forest anomaly detection.
    """
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or TRUST_WEIGHTS

    def evaluate_vehicle_trust(
        self,
        vehicle: Dict[str, Any],
        trust_info: Dict[str, Any],
        weights_override: Dict[str, float] = None
    ) -> Dict[str, Any]:
        w = weights_override or self.weights

        p = float(trust_info.get("position_consistency", 0.90))
        c = float(trust_info.get("movement_consistency", 0.90))
        f = float(trust_info.get("message_freshness", 0.95))
        s = float(trust_info.get("sensor_consistency", 0.90))

        # Clamp components [0, 1]
        p = max(0.0, min(1.0, p))
        c = max(0.0, min(1.0, c))
        f = max(0.0, min(1.0, f))
        s = max(0.0, min(1.0, s))

        # Base behavioural trust computation
        raw_trust = (
            w.get("w1_position", 0.35) * p +
            w.get("w2_movement", 0.25) * c +
            w.get("w3_freshness", 0.20) * f +
            w.get("w4_sensor", 0.20) * s
        )

        # Anomaly detection via Isolation Forest
        is_anomaly, anomaly_score, reasons = anomaly_detector.detect_anomaly(vehicle, trust_info)

        # Trust penalty if flagged by Isolation Forest
        if is_anomaly:
            penalty = 0.25 + max(0.0, -anomaly_score * 0.4)
            final_trust = max(0.05, raw_trust - penalty)
        else:
            final_trust = raw_trust

        final_trust = round(final_trust, 4)

        # Categorization
        if final_trust >= TRUST_THRESHOLDS["high"] and not is_anomaly:
            category = "High"
            recommended_handling = "Accept full telemetry into Digital Twin and Swarm"
        elif final_trust >= TRUST_THRESHOLDS["medium"] and not (is_anomaly and len(reasons) > 1):
            category = "Medium"
            recommended_handling = "Apply trust-weighted attenuation in local coordination"
        else:
            category = "Suspicious"
            recommended_handling = "Quarantine node: discard from corridor yielding calculations"

        return {
            "vehicle_id": vehicle.get("vehicle_id"),
            "computed_trust_score": float(final_trust),
            "raw_trust_score": float(raw_trust),
            "trust_category": category,
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": float(anomaly_score),
            "anomaly_reasons": list(reasons),
            "recommended_handling": recommended_handling,
            "components": {
                "position_consistency": float(p),
                "movement_consistency": float(c),
                "message_freshness": float(f),
                "sensor_consistency": float(s)
            },
            "weights_used": w
        }


trust_engine = TrustEngine()
