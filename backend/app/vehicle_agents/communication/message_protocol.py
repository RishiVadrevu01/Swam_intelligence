from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class V2XMessagePayload(BaseModel):
    sender_id: str
    receiver_id: str = "BROADCAST"
    message_type: str  # "TELEMETRY_BEACON", "EMERGENCY_ANNOUNCEMENT", "DPSO_CANDIDATE_SHARE", "REPLANNING_ALERT"
    timestamp: float
    sequence_number: int
    public_key_pem: Optional[str] = None
    signature_hex: Optional[str] = None
    signature_status: str = "UNSIGNED"
    data: Dict[str, Any] = Field(default_factory=dict)


class TelemetryBeaconData(BaseModel):
    latitude: float
    longitude: float
    speed: float
    acceleration: float
    heading: float
    current_lane: int
    road_id: str
    vehicle_type: str = "Sedan"


class EmergencyAnnouncementData(BaseModel):
    emergency_vehicle_id: str = "EV01"
    priority_level: int = 1
    target_lane: int = 2  # Center lane intended for corridor
    destination: str
    intended_route: List[str]
    estimated_speed: float = 62.5


class DPSOCandidateShareData(BaseModel):
    vehicle_id: str
    candidate_action: str  # "MOVE_LEFT", "MOVE_RIGHT", "REDUCE_SPEED", "MAINTAIN_GAP", "MAINTAIN_POSITION"
    target_lane: int
    local_fitness: float
    personal_best_fitness: float
    iteration: int


class ReplanningAlertData(BaseModel):
    blocked_vehicle_id: str
    blocked_road_id: str
    reason: str
    new_route: List[str]

