import time
from typing import Dict, List, Any, Optional


class AgentLocalDigitalTwin:
    """
    Independent Local Digital Twin instance maintained onboard each individual vehicle agent.
    Represents the agent's localized view of nearby traffic, emergency vehicle status,
    trust scores, driver compliance, and trajectory forecasts.
    """

    def __init__(self, vehicle_id: str, initial_state: Dict[str, Any]):
        self.vehicle_id = vehicle_id
        self.own_position = {
            "latitude": float(initial_state.get("latitude", 0.0)),
            "longitude": float(initial_state.get("longitude", 0.0))
        }
        self.own_speed = float(initial_state.get("speed", 40.0))
        self.own_acceleration = float(initial_state.get("acceleration", 0.0))
        self.own_heading = float(initial_state.get("heading", 48.0))
        self.own_lane = int(initial_state.get("current_lane", 2))
        self.road_id = initial_state.get("road_id", "ROAD_01")

        # Emergency vehicle status
        self.emergency_vehicle_position: Optional[Dict[str, float]] = None
        self.emergency_vehicle_distance: Optional[float] = None
        self.emergency_corridor_active: bool = False
        self.emergency_target_lane: int = 2

        # Neighbor perception (only within DSRC range < 450m)
        self.nearby_vehicles: Dict[str, Dict[str, Any]] = {}
        # Trust scores of neighbors
        self.trust_scores: Dict[str, float] = {}
        # Driver compliance probabilities of neighbors
        self.compliance_probabilities: Dict[str, float] = {}
        # Trajectories predicted for neighbors & self
        self.predicted_trajectories: Dict[str, List[Dict[str, float]]] = {}
        # Recommended movement action
        self.recommended_action: Optional[Dict[str, Any]] = None

        self.last_update_timestamp = time.time()
        self.is_stale = False
        self.history: List[Dict[str, Any]] = []

    def update_own_telemetry(self, lat: float, lon: float, speed: float, accel: float, heading: float, lane: int, road_id: str):
        self.own_position = {"latitude": lat, "longitude": lon}
        self.own_speed = speed
        self.own_acceleration = accel
        self.own_heading = heading
        self.own_lane = lane
        self.road_id = road_id
        self.last_update_timestamp = time.time()
        self._record_snapshot()

    def update_emergency_status(self, ev_data: Dict[str, Any], distance: float):
        self.emergency_vehicle_position = {
            "latitude": ev_data.get("latitude"),
            "longitude": ev_data.get("longitude")
        }
        self.emergency_vehicle_distance = distance
        self.emergency_corridor_active = True
        self.emergency_target_lane = int(ev_data.get("target_lane", 2))

    def update_neighbor_state(
        self,
        neighbor_id: str,
        telemetry: Dict[str, Any],
        distance: float,
        trust_score: float,
        compliance_prob: Optional[float] = None
    ):
        """
        Integrates neighbor telemetry into Local Twin.
        If trust is suspicious (<0.45), marks as quarantined and down-weights influence.
        """
        self.trust_scores[neighbor_id] = trust_score
        if compliance_prob is not None:
            self.compliance_probabilities[neighbor_id] = compliance_prob

        entry = {
            "vehicle_id": neighbor_id,
            "latitude": telemetry.get("latitude"),
            "longitude": telemetry.get("longitude"),
            "speed": telemetry.get("speed", 0.0),
            "lane": telemetry.get("current_lane", 1),
            "heading": telemetry.get("heading", 48.0),
            "road_id": telemetry.get("road_id", ""),
            "distance_meters": round(distance, 1),
            "relative_speed": round(telemetry.get("speed", 0.0) - self.own_speed, 1),
            "trust_score": round(trust_score, 3),
            "is_trusted": trust_score >= 0.45,
            "compliance_prob": compliance_prob,
            "last_heard": time.time()
        }
        self.nearby_vehicles[neighbor_id] = entry

    def prune_stale_neighbors(self, max_stale_seconds: float = 20.0):
        now = time.time()
        stale_keys = [
            k for k, v in self.nearby_vehicles.items()
            if (now - v.get("last_heard", now)) > max_stale_seconds
        ]
        for k in stale_keys:
            del self.nearby_vehicles[k]
        self.is_stale = (now - self.last_update_timestamp) > max_stale_seconds

    def _record_snapshot(self):
        snapshot = {
            "timestamp": self.last_update_timestamp,
            "position": dict(self.own_position),
            "speed": self.own_speed,
            "lane": self.own_lane,
            "nearby_count": len(self.nearby_vehicles),
            "ev_distance": self.emergency_vehicle_distance
        }
        self.history.append(snapshot)
        if len(self.history) > 20:
            self.history.pop(0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vehicle_id": self.vehicle_id,
            "own_position": self.own_position,
            "own_speed": self.own_speed,
            "own_acceleration": self.own_acceleration,
            "own_heading": self.own_heading,
            "own_lane": self.own_lane,
            "road_id": self.road_id,
            "emergency_vehicle_position": self.emergency_vehicle_position,
            "emergency_vehicle_distance": round(self.emergency_vehicle_distance, 1) if self.emergency_vehicle_distance else None,
            "emergency_corridor_active": self.emergency_corridor_active,
            "nearby_vehicles": list(self.nearby_vehicles.values()),
            "nearby_count": len(self.nearby_vehicles),
            "trust_scores": self.trust_scores,
            "driver_compliance_probabilities": self.compliance_probabilities,
            "predicted_trajectories": self.predicted_trajectories,
            "recommended_action": self.recommended_action,
            "last_update_timestamp": self.last_update_timestamp,
            "is_stale": self.is_stale,
            "history_count": len(self.history),
            "recent_history": self.history[-5:] if self.history else []
        }

