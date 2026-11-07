import time
from typing import Dict, Any, List, Optional
from app.vehicle_agents.base_agent import BaseVehicleAgent
from app.core.astar_router import astar_router
from app.vehicle_agents.communication.peer_network import peer_network


class EmergencyVehicleAgent(BaseVehicleAgent):
    """
    Emergency Vehicle Agent (e.g., Ambulance EV01).
    - Broadcasts cryptographically signed Emergency Priority Announcements.
    - Operates A* graph route planning.
    - Receives REPLANNING_ALERT from obstructed peers and executes real-time dynamic replanning.
    - Measures actual travel time T_e and corridor establishment metrics.
    """

    def __init__(self, vehicle_id: str, initial_data: Dict[str, Any]):
        super().__init__(vehicle_id, initial_data, role="EMERGENCY_VEHICLE")
        self.priority_level = int(initial_data.get("priority_level", 1))
        self.target_corridor_lane = int(initial_data.get("target_lane", 2))
        self.destination = initial_data.get("destination", "INT_5 (Hospital Junction)")

        self.start_node = "INT_1"
        self.destination_node = "INT_5"

        # Initial A* route plan
        self.active_route: Dict[str, Any] = astar_router.find_route(self.start_node, self.destination_node)
        self.original_route: Dict[str, Any] = dict(self.active_route)
        self.replan_events: List[Dict[str, Any]] = []
        self.corridor_status = "INITIALIZING"

        # Benchmark timers
        self.dispatch_start_time = time.time()
        self.corridor_formation_time_s: Optional[float] = None
        self.is_cleared = False

    def step(self, dt: float = 1.0):
        # 1. Broadcast signed EMERGENCY_ANNOUNCEMENT to all peers within range
        announcement_payload = {
            "message_type": "EMERGENCY_ANNOUNCEMENT",
            "data": {
                "emergency_vehicle_id": self.vehicle_id,
                "priority_level": self.priority_level,
                "target_lane": self.target_corridor_lane,
                "destination": self.destination,
                "intended_route": self.active_route.get("road_ids", []),
                "route_nodes": self.active_route.get("route_nodes", []),
                "latitude": self.state.latitude,
                "longitude": self.state.longitude,
                "speed": self.state.speed
            }
        }
        signed_announcement = self.authenticator.sign_message(announcement_payload, sequence_number=self.seq_counter)
        self.seq_counter += 1
        peer_network.broadcast(
            sender_id=self.vehicle_id,
            sender_lat=self.state.latitude,
            sender_lon=self.state.longitude,
            message=signed_announcement
        )

        # 2. Process incoming verified messages from peers
        while self.inbox:
            item = self.inbox.pop(0)
            msg = item["message"]
            msg_type = msg.get("message_type")
            data = msg.get("data", {})

            if msg_type == "REPLANNING_ALERT":
                self._handle_replanning_alert(data)
            elif msg_type == "TELEMETRY_BEACON":
                # Ingest neighbor telemetry into EV's local twin
                self.local_twin.update_neighbor_state(
                    neighbor_id=msg.get("sender_id"),
                    telemetry=data,
                    distance=item["distance"],
                    trust_score=0.95
                )

        # 3. Check corridor clearance state
        self._check_corridor_clearance()

        # Update EV Local Twin
        self.local_twin.update_own_telemetry(
            lat=self.state.latitude,
            lon=self.state.longitude,
            speed=self.state.speed,
            accel=self.state.acceleration,
            heading=self.state.heading,
            lane=self.state.current_lane,
            road_id=self.state.road_id
        )

    def _handle_replanning_alert(self, alert_data: Dict[str, Any]):
        """
        Triggered when a peer broadcasts a verified REPLANNING_ALERT.
        Re-weights the blocked road segment and executes dynamic A* route replanning.
        """
        blocked_road = alert_data.get("blocked_road_id", "ROAD_02")
        blocked_vehicle = alert_data.get("blocked_vehicle_id", "UNKNOWN")

        # Execute dynamic replanning via A* Search
        replan_res = astar_router.simulate_dynamic_replan(
            original_route=self.original_route,
            failed_vehicle_id=blocked_vehicle,
            blocked_road_id=blocked_road
        )

        self.active_route = replan_res["updated_route"]
        self.corridor_status = "REPLANNING"

        replan_record = {
            "timestamp": time.time(),
            "blocked_vehicle_id": blocked_vehicle,
            "blocked_road_id": blocked_road,
            "new_route_nodes": self.active_route.get("route_nodes", []),
            "time_delta_seconds": replan_res.get("travel_time_delta_seconds", 0.0),
            "reason": alert_data.get("reason", "Corridor blockage detected")
        }
        self.replan_events.append(replan_record)

    def _check_corridor_clearance(self):
        """
        Monitors whether vehicles along the target lane have cleared the corridor.
        """
        target_lane = self.target_corridor_lane
        corridor_blocked = False

        for n in self.local_twin.nearby_vehicles.values():
            if int(n.get("lane", 1)) == target_lane and float(n.get("distance_meters", 100.0)) < 180.0:
                corridor_blocked = True
                break

        if not corridor_blocked and not self.is_cleared:
            self.corridor_status = "ACTIVE"
            self.is_cleared = True
            if self.corridor_formation_time_s is None:
                self.corridor_formation_time_s = round(time.time() - self.dispatch_start_time, 2)
        elif corridor_blocked:
            self.corridor_status = "COORDINATING"
            self.is_cleared = False

