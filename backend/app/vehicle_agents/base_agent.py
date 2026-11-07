import abc
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.vehicle_agents.security.identity import AgentIdentity
from app.vehicle_agents.security.authentication import AgentAuthenticator
from app.vehicle_agents.digital_twin.local_twin import AgentLocalDigitalTwin
from app.vehicle_agents.trust.trust_engine import AgentTrustEvaluator
from app.vehicle_agents.coordination.distributed_dpso import DistributedDPSOCoordinator
from app.vehicle_agents.communication.peer_network import peer_network
from app.core.trajectory_predictor import trajectory_predictor
from app.core.compliance_predictor import compliance_predictor


class VehicleState(BaseModel):
    vehicle_id: str
    latitude: float
    longitude: float
    speed: float
    acceleration: float
    heading: float
    current_lane: int
    road_id: str
    vehicle_type: str = "Sedan"
    is_active: bool = True


class BaseVehicleAgent(abc.ABC):
    """
    Abstract Base Class for an independent virtual vehicle agent.
    Each agent acts as an autonomous On-Board Unit (OBU) maintaining:
    - Independent state
    - Cryptographic identity (ECDSA P-256)
    - Local Digital Twin (LDT)
    - Trust evaluation & Anomaly screening
    - Distributed Swarm Coordination (DPSO)
    - Local yielding decisions
    """

    def __init__(self, vehicle_id: str, initial_data: Dict[str, Any], role: str = "NORMAL_VEHICLE"):
        self.vehicle_id = vehicle_id
        self.role = role
        self.seq_counter: int = 1

        self.state = VehicleState(
            vehicle_id=vehicle_id,
            latitude=float(initial_data.get("latitude", 37.778)),
            longitude=float(initial_data.get("longitude", -122.418)),
            speed=float(initial_data.get("speed", 40.0)),
            acceleration=float(initial_data.get("acceleration", 0.0)),
            heading=float(initial_data.get("heading", 48.0)),
            current_lane=int(initial_data.get("current_lane", 2)),
            road_id=initial_data.get("road_id", "ROAD_01"),
            vehicle_type=initial_data.get("vehicle_type", "Sedan"),
            is_active=True
        )

        # Independent agent modules
        self.identity = AgentIdentity(vehicle_id=vehicle_id, role=role)
        self.authenticator = AgentAuthenticator(identity=self.identity)
        self.local_twin = AgentLocalDigitalTwin(vehicle_id=vehicle_id, initial_state=initial_data)
        self.trust_evaluator = AgentTrustEvaluator()
        self.dpso = DistributedDPSOCoordinator(vehicle_id=vehicle_id)

        # Buffer for incoming verified neighbor messages
        self.inbox: List[Dict[str, Any]] = []
        self.received_neighbor_candidates: List[Dict[str, Any]] = []

        # Local yielding state
        self.current_recommendation: Optional[Dict[str, Any]] = None
        self.driver_compliance_probability: float = 0.85
        self.is_compliant: bool = True
        self.response_timer_seconds: float = 0.0
        self.failed_yielding_detected: bool = False

        # Register in decentralized P2P network
        peer_network.register_agent(self)

    @property
    def digital_twin(self) -> AgentLocalDigitalTwin:
        return self.local_twin

    @property
    def dpso_coordinator(self) -> DistributedDPSOCoordinator:
        return self.dpso

    def receive_v2x_message(self, message: Dict[str, Any], distance: float):
        """
        Invoked by peer_network when an over-the-air packet arrives within neighborhood range.
        Applies cryptographic verification and sequence replay detection immediately.
        """
        is_valid, reason = self.authenticator.verify_message(message)
        if not is_valid:
            # Drop unauthenticated / replayed / stale message
            return

        # Store authenticated message with reception metadata
        self.inbox.append({
            "message": message,
            "distance": distance,
            "received_at": time.time()
        })

    def broadcast_beacon(self):
        """
        Generates and cryptographically signs a periodic telemetry beacon,
        then transmits it to neighboring peers in N_i(t).
        """
        payload = {
            "message_type": "TELEMETRY_BEACON",
            "data": {
                "latitude": self.state.latitude,
                "longitude": self.state.longitude,
                "speed": self.state.speed,
                "acceleration": self.state.acceleration,
                "heading": self.state.heading,
                "current_lane": self.state.current_lane,
                "road_id": self.state.road_id,
                "vehicle_type": self.state.vehicle_type
            }
        }
        signed_msg = self.authenticator.sign_message(payload, sequence_number=self.seq_counter)
        self.seq_counter += 1

        peer_network.broadcast(
            sender_id=self.vehicle_id,
            sender_lat=self.state.latitude,
            sender_lon=self.state.longitude,
            message=signed_msg
        )

    def process_inbox(self):
        """
        Processes accepted, cryptographically verified packets:
        - Evaluates behavioral trust T_i = w_p*P_i + w_c*C_i + w_f*F_i + w_s*S_i
        - Updates Local Digital Twin
        - Ingests emergency announcements or DPSO candidate shares
        """
        while self.inbox:
            item = self.inbox.pop(0)
            msg = item["message"]
            distance = item["distance"]
            sender_id = msg.get("sender_id")
            msg_type = msg.get("message_type")
            data = msg.get("data", {})

            if msg_type == "TELEMETRY_BEACON":
                # Behavioral Trust Evaluation
                t_res = self.trust_evaluator.compute_trust(
                    peer_vehicle_state=data,
                    raw_telemetry=data,
                    message_age_seconds=time.time() - msg.get("timestamp", time.time())
                )
                t_score = t_res["computed_trust_score"]

                # Update Local Twin
                self.local_twin.update_neighbor_state(
                    neighbor_id=sender_id,
                    telemetry=data,
                    distance=distance,
                    trust_score=t_score
                )

            elif msg_type == "EMERGENCY_ANNOUNCEMENT":
                self.local_twin.update_emergency_status(data, distance=distance)

            elif msg_type == "DPSO_CANDIDATE_SHARE":
                self.received_neighbor_candidates.append(data)

        # Prune stale neighbors
        self.local_twin.prune_stale_neighbors()

    @abc.abstractmethod
    def step(self, dt: float = 1.0):
        """
        Executes one local autonomous step of the agent.
        """
        pass

    def get_public_summary(self) -> Dict[str, Any]:
        """
        Provides public read-only state for monitoring gateway / dashboard without
        exposing private keys or centralizing decisions.
        """
        return {
            "vehicle_id": self.vehicle_id,
            "role": self.role,
            "state": self.state.dict(),
            "local_twin": self.local_twin.to_dict(),
            "current_recommendation": self.current_recommendation,
            "driver_compliance_probability": round(self.driver_compliance_probability, 3),
            "is_compliant": self.is_compliant,
            "failed_yielding_detected": self.failed_yielding_detected,
            "security_events_count": len(self.authenticator.security_log),
            "recent_security_event": self.authenticator.security_log[-1] if self.authenticator.security_log else None
        }

