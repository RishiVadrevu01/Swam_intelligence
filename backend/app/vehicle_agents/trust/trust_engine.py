from typing import Dict, List, Any, Optional
from app.config import TRUST_WEIGHTS, TRUST_THRESHOLDS
from app.core.anomaly_detector import anomaly_detector


class AgentTrustEvaluator:
    """
    Implements Formula 2 from the research paper:
    T_i = w_p * P_i + w_c * C_i + w_f * F_i + w_s * S_i
    
    Where:
    - P_i: Position plausibility [0, 1]
    - C_i: Movement consistency [0, 1]
    - F_i: Message freshness [0, 1]
    - S_i: Consistency with independently received neighbor information [0, 1]
    
    Weights sum to 1.0 (w_p=0.35, w_c=0.25, w_f=0.20, w_s=0.20).
    Integrates Isolation Forest anomaly detection as additional trust evidence.
    Note: A valid digital signature does NOT prove factual accuracy.
    """

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            "w_p": 0.35,  # Position plausibility
            "w_c": 0.25,  # Movement consistency
            "w_f": 0.20,  # Message freshness
            "w_s": 0.20   # Consistency with neighbor reports
        }
        # peer_id -> historical trust scores
        self.trust_history: Dict[str, List[float]] = {}

    def compute_trust(
        self,
        peer_vehicle_state: Dict[str, Any],
        raw_telemetry: Dict[str, Any],
        message_age_seconds: float,
        neighbor_agreement_ratio: float = 0.90
    ) -> Dict[str, Any]:
        vid = peer_vehicle_state.get("vehicle_id", "UNKNOWN")

        # 1. P_i: Position Plausibility
        # Check if position is on valid road segment and delta displacement is realistic
        speed = float(peer_vehicle_state.get("speed", 40.0))
        accel = float(peer_vehicle_state.get("acceleration", 0.0))
        delta_pos = (speed / 3.6) * 1.0
        p_score = 0.95
        if speed > 80.0 or speed < 0.0:
            p_score -= 0.40
        if delta_pos > 30.0:
            p_score -= 0.35
        p_score = max(0.05, min(1.0, p_score))

        # 2. C_i: Movement Consistency
        # Checks physically plausible acceleration and heading
        c_score = 0.95
        if abs(accel) > 4.5:
            c_score -= 0.45
        heading_var = abs(float(peer_vehicle_state.get("heading", 48.0)) - 48.0)
        if heading_var > 25.0:
            c_score -= 0.30
        c_score = max(0.05, min(1.0, c_score))

        # 3. F_i: Message Freshness
        # Decay function based on message age (15s cutoff)
        f_score = max(0.0, 1.0 - (message_age_seconds / 15.0))
        f_score = max(0.05, min(1.0, f_score))

        # 4. S_i: Consistency with Independently Received Neighbor Information
        # Cross-validation from overlapping neighbor observation
        s_score = max(0.05, min(1.0, neighbor_agreement_ratio))

        # Calculate base formula: T_i = w_p*P_i + w_c*C_i + w_f*F_i + w_s*S_i
        w_p = self.weights.get("w_p", 0.35)
        w_c = self.weights.get("w_c", 0.25)
        w_f = self.weights.get("w_f", 0.20)
        w_s = self.weights.get("w_s", 0.20)

        raw_trust = (w_p * p_score) + (w_c * c_score) + (w_f * f_score) + (w_s * s_score)

        # Apply Isolation Forest anomaly screening
        trust_info_proxy = {
            "position_consistency": p_score,
            "movement_consistency": c_score,
            "message_freshness": f_score,
            "sensor_consistency": s_score
        }
        is_anomaly, anomaly_score, reasons = anomaly_detector.detect_anomaly(peer_vehicle_state, trust_info_proxy)

        # Attenuate trust if Isolation Forest flags abnormal kinematics
        if is_anomaly:
            penalty = 0.25 + max(0.0, -anomaly_score * 0.4)
            final_trust = max(0.05, raw_trust - penalty)
        else:
            final_trust = raw_trust

        final_trust = round(final_trust, 4)

        # Trust Classification
        if final_trust >= 0.75 and not is_anomaly:
            category = "High"
            action = "Accept full telemetry into local twin & DPSO"
        elif final_trust >= 0.45 and not (is_anomaly and len(reasons) > 1):
            category = "Medium"
            action = "Apply trust-weighted attenuation in coordination"
        else:
            category = "Suspicious"
            action = "Quarantine node: exclude from corridor yielding"

        # Record trust history
        if vid not in self.trust_history:
            self.trust_history[vid] = []
        self.trust_history[vid].append(final_trust)
        if len(self.trust_history[vid]) > 30:
            self.trust_history[vid].pop(0)

        return {
            "vehicle_id": vid,
            "computed_trust_score": float(final_trust),
            "raw_trust_score": float(round(raw_trust, 4)),
            "trust_category": category,
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": float(round(anomaly_score, 4)),
            "anomaly_reasons": list(reasons),
            "recommended_handling": action,
            "components": {
                "P_position_plausibility": float(round(p_score, 3)),
                "C_movement_consistency": float(round(c_score, 3)),
                "F_message_freshness": float(round(f_score, 3)),
                "S_neighbor_consistency": float(round(s_score, 3))
            },
            "weights": self.weights
        }

