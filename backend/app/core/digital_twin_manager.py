import time
import math
from typing import Dict, List, Any, Optional


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class LocalDigitalTwin:
    """
    Independent Local Digital Twin instance maintained onboard each individual vehicle.
    Represents the vehicle's localized perception of surrounding nodes, emergency vehicles,
    trust scores, and predicted trajectories.
    """
    def __init__(self, vehicle_id: str, initial_data: Dict[str, Any]):
        self.vehicle_id = vehicle_id
        self.own_position = {
            "latitude": initial_data.get("latitude", 0.0),
            "longitude": initial_data.get("longitude", 0.0)
        }
        self.own_speed = float(initial_data.get("speed", 40.0))
        self.own_heading = float(initial_data.get("heading", 48.0))
        self.own_lane = int(initial_data.get("current_lane", 2))
        self.road_id = initial_data.get("road_id", "ROAD_01")

        self.emergency_vehicle_position: Optional[Dict[str, float]] = None
        self.emergency_vehicle_distance: Optional[float] = None

        # Local perceptions of neighbors within communication/sensor range (~450 meters)
        self.nearby_vehicles: List[Dict[str, Any]] = []
        self.nearby_road_segments: List[str] = [self.road_id]

        # Trajectories predicted locally for self and neighbors
        self.predicted_trajectories: Dict[str, List[Dict[str, float]]] = {}

        # Locally maintained trust scores for neighbors
        self.trust_scores: Dict[str, float] = {}

        # Locally maintained compliance estimates
        self.driver_compliance_probabilities: Dict[str, float] = {}

        self.last_update_timestamp = time.time()
        self.is_stale = False
        self.history: List[Dict[str, Any]] = []

    def update_own_telemetry(self, lat: float, lon: float, speed: float, heading: float, lane: int, road_id: str):
        self.own_position = {"latitude": lat, "longitude": lon}
        self.own_speed = speed
        self.own_heading = heading
        self.own_lane = lane
        self.road_id = road_id
        self.last_update_timestamp = time.time()
        self._record_snapshot()

    def update_emergency_vehicle(self, ev_data: Dict[str, Any]):
        ev_lat = ev_data.get("latitude")
        ev_lon = ev_data.get("longitude")
        if ev_lat is not None and ev_lon is not None:
            self.emergency_vehicle_position = {"latitude": ev_lat, "longitude": ev_lon}
            self.emergency_vehicle_distance = haversine_distance_meters(
                self.own_position["latitude"], self.own_position["longitude"],
                ev_lat, ev_lon
            )

    def integrate_neighbor_telemetry(
        self,
        neighbor_id: str,
        telemetry: Dict[str, Any],
        trust_score: float,
        compliance_prob: Optional[float] = None,
        communication_range: float = 450.0
    ):
        """
        Integrates telemetry received from a neighbor vehicle, weighted by its evaluated trust score.
        If trust is too low, the information is attenuated or ignored.
        """
        n_lat = telemetry.get("latitude", 0.0)
        n_lon = telemetry.get("longitude", 0.0)
        dist = haversine_distance_meters(
            self.own_position["latitude"], self.own_position["longitude"],
            n_lat, n_lon
        )

        # Only retain vehicles within localized DSRC / C-V2X communication range
        if dist > communication_range:
            # Remove if previously nearby
            self.nearby_vehicles = [v for v in self.nearby_vehicles if v["vehicle_id"] != neighbor_id]
            return

        self.trust_scores[neighbor_id] = trust_score
        if compliance_prob is not None:
            self.driver_compliance_probabilities[neighbor_id] = compliance_prob

        # Trust-weighted neighbor representation:
        # If trust is below 0.40, mark as untrusted / quarantine in local twin
        neighbor_entry = {
            "vehicle_id": neighbor_id,
            "latitude": n_lat,
            "longitude": n_lon,
            "speed": telemetry.get("speed", 0.0),
            "lane": telemetry.get("current_lane", 1),
            "distance_meters": round(dist, 1),
            "relative_speed": round(telemetry.get("speed", 0.0) - self.own_speed, 1),
            "trust_score": round(trust_score, 3),
            "is_trusted": trust_score >= 0.45,
            "compliance_prob": compliance_prob,
            "last_heard": time.time()
        }

        # Update or append
        existing = next((i for i, v in enumerate(self.nearby_vehicles) if v["vehicle_id"] == neighbor_id), None)
        if existing is not None:
            self.nearby_vehicles[existing] = neighbor_entry
        else:
            self.nearby_vehicles.append(neighbor_entry)

        # Sort nearby vehicles by spatial proximity
        self.nearby_vehicles.sort(key=lambda x: x["distance_meters"])

    def check_staleness(self, stale_threshold_seconds: float = 20.0):
        now = time.time()
        self.is_stale = (now - self.last_update_timestamp) > stale_threshold_seconds

        # Prune stale neighbors
        self.nearby_vehicles = [
            v for v in self.nearby_vehicles
            if (now - v.get("last_heard", now)) <= stale_threshold_seconds
        ]

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
            "own_heading": self.own_heading,
            "own_lane": self.own_lane,
            "road_id": self.road_id,
            "emergency_vehicle_position": self.emergency_vehicle_position,
            "emergency_vehicle_distance": round(self.emergency_vehicle_distance, 1) if self.emergency_vehicle_distance else None,
            "nearby_vehicles": self.nearby_vehicles,
            "nearby_road_segments": self.nearby_road_segments,
            "predicted_trajectories": self.predicted_trajectories,
            "trust_scores": self.trust_scores,
            "driver_compliance_probabilities": self.driver_compliance_probabilities,
            "last_update_timestamp": self.last_update_timestamp,
            "is_stale": self.is_stale,
            "history_count": len(self.history),
            "recent_history": self.history[-5:] if self.history else []
        }


class DigitalTwinManager:
    """
    Manages collection of independent Local Digital Twins across all vehicles.
    """
    def __init__(self):
        self.twins: Dict[str, LocalDigitalTwin] = {}

    def initialize_twins(self, vehicles: List[Dict[str, Any]], emergency_vehicle: Dict[str, Any], trust_map: Dict[str, float] = None):
        self.twins.clear()
        trust_map = trust_map or {}

        # 1. Instantiate every vehicle's independent twin
        for v in vehicles:
            vid = v["vehicle_id"]
            self.twins[vid] = LocalDigitalTwin(vid, v)
            if emergency_vehicle:
                self.twins[vid].update_emergency_vehicle(emergency_vehicle)

        # 2. Local neighbor discovery and trust-weighted telemetry integration for every twin
        for vid, twin in self.twins.items():
            for other_v in vehicles:
                other_id = other_v["vehicle_id"]
                if other_id == vid:
                    continue
                t_score = trust_map.get(other_id, 0.85)
                twin.integrate_neighbor_telemetry(other_id, other_v, t_score)

    def get_twin(self, vehicle_id: str) -> Optional[LocalDigitalTwin]:
        return self.twins.get(vehicle_id)

    def get_all_twins_summary(self) -> List[Dict[str, Any]]:
        return [twin.to_dict() for twin in self.twins.values()]


digital_twin_manager = DigitalTwinManager()
