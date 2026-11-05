from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Position(BaseModel):
    latitude: float
    longitude: float


class EmergencyVehicle(BaseModel):
    emergency_vehicle_id: str
    vehicle_type: str = "Ambulance"
    latitude: float
    longitude: float
    speed: float  # km/h
    heading: float  # degrees
    destination: str
    priority_level: int = 1
    emergency_status: str = "ACTIVE_DISPATCH"
    intended_route: List[str] = Field(default_factory=list)
    current_road_id: Optional[str] = None
    target_lane: int = 1


class NormalVehicle(BaseModel):
    vehicle_id: str
    latitude: float
    longitude: float
    speed: float  # km/h
    acceleration: float  # m/s^2
    heading: float  # degrees
    current_lane: int  # 1: Left, 2: Center, 3: Right
    vehicle_type: str = "Sedan"
    movement_direction: str = "Northbound"
    destination: str
    driver_id: str
    road_id: str
    distance_along_road: float = 0.0


class RoadSegment(BaseModel):
    road_id: str
    name: str
    start_intersection: str
    end_intersection: str
    length_meters: float
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    lanes: int = 3
    traffic_density: float  # vehicles/km
    average_speed: float  # km/h
    road_capacity: int = 60
    congestion_level: str  # Low, Moderate, High, Severe
    available_space: float  # percentage 0 - 100%
    road_direction: str = "Northbound"


class DriverBehaviour(BaseModel):
    vehicle_id: str
    previous_yielding_actions: int
    current_yielding_status: str  # "YIELDED", "YIELDING", "MAINTAINING", "NON_YIELDING"
    response_time: float  # seconds
    lane_change_history: List[str] = Field(default_factory=list)
    acceleration_history: List[float] = Field(default_factory=list)
    driver_compliance_label: str  # "High", "Medium", "Low"


class VehicleTrustInfo(BaseModel):
    vehicle_id: str
    position_consistency: float  # 0.0 - 1.0
    movement_consistency: float  # 0.0 - 1.0
    message_freshness: float     # 0.0 - 1.0
    sensor_consistency: float    # 0.0 - 1.0
    historical_trust_score: float
    computed_trust_score: float = 0.0
    trust_category: str = "High"  # "High", "Medium", "Suspicious"
    is_anomaly: bool = False
    anomaly_reasons: List[str] = Field(default_factory=list)
    recommended_handling: str = "Accept"


class V2XMessage(BaseModel):
    sender_id: str
    receiver_id: str = "BROADCAST"
    message_type: str = "EMERGENCY_ANNOUNCEMENT"  # or "TELEMETRY_BEACON", "COORDINATION_ACK"
    timestamp: float
    sequence_number: int
    signature_status: str = "PENDING"
    signature_hex: Optional[str] = None
    public_key_pem: Optional[str] = None
    message_content: Dict[str, Any]


class LocalDigitalTwinState(BaseModel):
    vehicle_id: str
    own_position: Position
    own_speed: float
    own_heading: float
    own_lane: int
    emergency_vehicle_position: Optional[Position] = None
    emergency_vehicle_distance: Optional[float] = None
    nearby_vehicles: List[Dict[str, Any]] = Field(default_factory=list)
    nearby_road_segments: List[str] = Field(default_factory=list)
    predicted_trajectories: Dict[str, List[Dict[str, float]]] = Field(default_factory=dict)
    trust_scores: Dict[str, float] = Field(default_factory=dict)
    driver_compliance_probabilities: Dict[str, float] = Field(default_factory=dict)
    last_update_timestamp: float
    is_stale: bool = False
    history_count: int = 0


class CompliancePredictionResult(BaseModel):
    vehicle_id: str
    yielding_probability: float
    compliance_class: str
    compliance_confidence: float
    contributing_features: Dict[str, float]
    raw_features: Dict[str, Any]


class TrajectoryPredictionResult(BaseModel):
    vehicle_id: str
    historical_points: List[Dict[str, float]]
    predicted_points: List[Dict[str, float]]
    uncertainty_radius_meters: float
    model_used: str = "LSTM"


class DPSOIterationResult(BaseModel):
    iteration: int
    best_fitness: float
    average_fitness: float


class VehicleMovementAction(BaseModel):
    vehicle_id: str
    current_lane: int
    recommended_lane: int
    action_type: str  # "MOVE_LEFT", "MOVE_RIGHT", "REDUCE_SPEED", "MAINTAIN_GAP", "MAINTAIN_POSITION"
    target_speed: float
    safety_margin_meters: float
    compliance_likelihood: float
    conflict_detected: bool = False
    reason: str


class DPSOResult(BaseModel):
    participating_agents: List[str]
    total_iterations: int
    initial_fitness: float
    best_fitness: float
    convergence_history: List[DPSOIterationResult]
    recommended_actions: List[VehicleMovementAction]
    conflicts_detected: int
    objective_breakdown: Dict[str, float]
    execution_time_ms: float


class RoutePlanResult(BaseModel):
    emergency_vehicle_id: str
    start_node: str
    destination_node: str
    original_route_nodes: List[str]
    active_route_nodes: List[str]
    route_coordinates: List[List[float]]
    total_distance_meters: float
    estimated_travel_time_seconds: float
    replanning_occurred: bool = False
    replanning_reason: Optional[str] = None


class EmergencyCorridorStatus(BaseModel):
    corridor_id: str
    emergency_vehicle: EmergencyVehicle
    status: str  # "INITIALIZING", "COORDINATING", "ACTIVE", "REPLANNING", "CLEARED"
    active_scenario: str
    participating_vehicle_count: int
    yielding_vehicles_count: int
    non_yielding_vehicles_count: int
    suspicious_vehicles_count: int
    average_delay_seconds: float
    corridor_establishment_time_seconds: float
    active_route: RoutePlanResult
    recommended_actions: List[VehicleMovementAction]
    recent_events: List[Dict[str, Any]]

