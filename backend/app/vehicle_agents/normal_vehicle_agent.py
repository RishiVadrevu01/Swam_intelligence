import time
from typing import Dict, Any, Optional
from app.vehicle_agents.base_agent import BaseVehicleAgent
from app.core.trajectory_predictor import trajectory_predictor
from app.core.compliance_predictor import compliance_predictor
from app.vehicle_agents.communication.peer_network import peer_network


class NormalVehicleAgent(BaseVehicleAgent):
    """
    Independent Normal Connected Vehicle Agent.
    Participates in decentralized corridor formation:
    - Broadcasts authenticated telemetry
    - Verifies neighbor beacons
    - Computes trust and maintains isolated Local Digital Twin
    - Evaluates driver compliance using XGBoost
    - Runs local DPSO swarm step
    - Monitors driver execution and triggers dynamic replanning alerts upon failure
    """

    def __init__(
        self,
        vehicle_id: str,
        initial_data: Dict[str, Any],
        driver_profile: Optional[Dict[str, Any]] = None
    ):
        super().__init__(vehicle_id, initial_data, role="NORMAL_VEHICLE")
        self.driver_profile = driver_profile or {
            "previous_yielding_actions": 6,
            "response_time": 2.2,
            "driver_compliance_label": "High"
        }
        self.max_yield_wait_time = float(self.driver_profile.get("response_time", 2.5)) + 1.5

    def step(self, dt: float = 1.0):
        # 1. Broadcast signed periodic telemetry beacon
        self.broadcast_beacon()

        # 2. Process authenticated inbox (update twin, trust)
        self.process_inbox()

        # 3. Forecast ego trajectory using PyTorch LSTM
        try:
            ego_dict = self.state.dict()
            traj_res = trajectory_predictor.predict_trajectory(ego_dict, steps=5)
            self.local_twin.predicted_trajectories[self.vehicle_id] = traj_res["predicted_points"]
        except Exception:
            pass

        # 4. If an Emergency Vehicle is within corridor range, coordinate yielding
        if self.local_twin.emergency_corridor_active:
            ev_dist = self.local_twin.emergency_vehicle_distance or 200.0

            # Predict driver yielding compliance with XGBoost
            comp_res = compliance_predictor.predict_compliance(
                vehicle=self.state.dict(),
                behaviour=self.driver_profile,
                ev_distance=ev_dist
            )
            self.driver_compliance_probability = comp_res["yielding_probability"]

            # Run local DPSO swarm step
            ev_summary = {
                "active": self.local_twin.emergency_corridor_active,
                "target_lane": self.local_twin.emergency_target_lane,
                "distance": ev_dist
            }
            ego_summary = self.state.dict()
            ego_summary["distance_to_ev"] = ev_dist

            neighbors_list = list(self.local_twin.nearby_vehicles.values())
            dpso_res = self.dpso.step_distributed_dpso(
                ego_state=ego_summary,
                ev_state=ev_summary,
                neighbor_states=neighbors_list,
                neighbor_candidates=self.received_neighbor_candidates,
                driver_compliance_prob=self.driver_compliance_probability,
                trust_scores=self.local_twin.trust_scores
            )
            self.current_recommendation = dpso_res
            self.local_twin.recommended_action = dpso_res

            # Broadcast DPSO candidate share to local neighbors
            share_payload = {
                "message_type": "DPSO_CANDIDATE_SHARE",
                "data": {
                    "vehicle_id": self.vehicle_id,
                    "candidate_action_idx": self.dpso.particle.p_best_action,
                    "personal_best_fitness": self.dpso.particle.p_best_fitness
                }
            }
            signed_share = self.authenticator.sign_message(share_payload, sequence_number=self.seq_counter)
            self.seq_counter += 1
            peer_network.broadcast(
                sender_id=self.vehicle_id,
                sender_lat=self.state.latitude,
                sender_lon=self.state.longitude,
                message=signed_share
            )
            self.received_neighbor_candidates.clear()

            # 5. Monitor Driver Response & Detect Non-Compliance
            self._simulate_driver_response(dt)

        # Update Local Twin ego state
        self.local_twin.update_own_telemetry(
            lat=self.state.latitude,
            lon=self.state.longitude,
            speed=self.state.speed,
            accel=self.state.acceleration,
            heading=self.state.heading,
            lane=self.state.current_lane,
            road_id=self.state.road_id
        )

    def _simulate_driver_response(self, dt: float):
        """
        Simulates whether the driver actually follows the yielding directive.
        If non-compliant, flags failed yielding and broadcasts a REPLANNING_ALERT.
        """
        rec_action = self.current_recommendation.get("recommended_action") if self.current_recommendation else None
        if not rec_action or rec_action == "MAINTAIN_POSITION":
            return

        # Check if driver refuses to yield (e.g. low compliance label or low probability)
        is_cooperative = (self.driver_compliance_probability >= 0.40) and (self.driver_profile.get("driver_compliance_label") != "Low")

        self.response_timer_seconds += dt

        if is_cooperative:
            # Yield: transition to recommended lane
            rec_lane = self.current_recommendation.get("recommended_lane", self.state.current_lane)
            if self.response_timer_seconds >= 1.0:
                self.state.current_lane = rec_lane
                self.is_compliant = True
                self.failed_yielding_detected = False
        else:
            # Driver refuses or fails to yield
            if self.response_timer_seconds > self.max_yield_wait_time:
                self.is_compliant = False
                self.failed_yielding_detected = True

                # Broadcast REPLANNING_ALERT to notify peers and emergency vehicle
                alert_payload = {
                    "message_type": "REPLANNING_ALERT",
                    "data": {
                        "blocked_vehicle_id": self.vehicle_id,
                        "blocked_road_id": self.state.road_id,
                        "blocked_lane": self.state.current_lane,
                        "reason": f"Driver {self.vehicle_id} failed to yield within {self.response_timer_seconds:.1f}s window"
                    }
                }
                signed_alert = self.authenticator.sign_message(alert_payload, sequence_number=self.seq_counter)
                self.seq_counter += 1
                peer_network.broadcast(
                    sender_id=self.vehicle_id,
                    sender_lat=self.state.latitude,
                    sender_lon=self.state.longitude,
                    message=signed_alert
                )

