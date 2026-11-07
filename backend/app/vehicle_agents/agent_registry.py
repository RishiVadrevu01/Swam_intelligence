import json
import time
from typing import Dict, List, Any, Optional
from app.config import DATA_DIR
from app.vehicle_agents.normal_vehicle_agent import NormalVehicleAgent
from app.vehicle_agents.emergency_vehicle_agent import EmergencyVehicleAgent
from app.vehicle_agents.communication.peer_network import peer_network
from app.core.scenario_generator import scenario_gen


class VehicleAgentRegistry:
    """
    Decentralized Vehicle Agent Registry & Lifecycle Manager.
    - Instantiates truly independent vehicle agents (Normal + Emergency).
    - Coordinates asynchronous simulation time-steps where each agent acts independently.
    - Supports fault injection (agent failure & recovery testing).
    - Serves as the read-only monitoring gateway for the frontend dashboard.
    """

    def __init__(self):
        self.normal_agents: Dict[str, NormalVehicleAgent] = {}
        self.emergency_agent: Optional[EmergencyVehicleAgent] = None
        self.active_scenario: str = "Scenario A: Normal Traffic"
        self.current_step: int = 0
        self.last_step_time: float = time.time()

    def initialize_from_scenario(self, scenario_name: str = "Scenario A: Normal Traffic", seed: int = 42):
        """
        Creates independent agent instances from scenario data.
        """
        self.active_scenario = scenario_name
        scenario_gen.seed = seed
        scenario_gen.generate_scenario(scenario_name)

        # Clear existing agents
        self.normal_agents.clear()
        peer_network.registered_agents.clear()
        peer_network.offline_agents.clear()

        def _safe_load(filename: str, default: Any):
            p = DATA_DIR / filename
            try:
                if p.exists() and p.stat().st_size > 0:
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception:
                pass
            return default

        # Load generated datasets safely
        v_list = _safe_load("vehicles.json", [])
        ev_list = _safe_load("emergency_vehicles.json", [])
        raw_b = _safe_load("driver_behaviour.json", [])
        b_list = {b["vehicle_id"]: b for b in raw_b}

        # 1. Instantiate independent Normal Vehicle Agents
        for v in v_list:
            vid = v["vehicle_id"]
            driver_profile = b_list.get(vid)
            agent = NormalVehicleAgent(
                vehicle_id=vid,
                initial_data=v,
                driver_profile=driver_profile
            )
            self.normal_agents[vid] = agent

        # 2. Instantiate independent Emergency Vehicle Agent (EV01)
        if ev_list:
            self.emergency_agent = EmergencyVehicleAgent(
                vehicle_id=ev_list[0].get("emergency_vehicle_id", "EV01"),
                initial_data=ev_list[0]
            )

        self.current_step = 0
        self.last_step_time = time.time()

    def step_all(self, dt: float = 1.0):
        """
        Simulates an asynchronous step where each autonomous agent independently:
        - Polls local sensors
        - Broadcasts V2V beacon
        - Ingests and cryptographically verifies peer beacons
        - Updates independent Local Digital Twin
        - Evaluates trust & AI predictions
        - Executes local DPSO swarm step
        """
        self.current_step += 1
        self.last_step_time = time.time()

        # 1. Emergency agent steps
        if self.emergency_agent:
            self.emergency_agent.step(dt)

        # 2. Normal agents step independently
        for agent in list(self.normal_agents.values()):
            agent.step(dt)

    def get_agent(self, vehicle_id: str) -> Optional[Any]:
        if self.emergency_agent and self.emergency_agent.vehicle_id == vehicle_id:
            return self.emergency_agent
        return self.normal_agents.get(vehicle_id)

    def set_agent_offline(self, vehicle_id: str, offline: bool = True):
        """
        Fault tolerance testing: temporarily disconnect an agent from the V2V network.
        """
        peer_network.set_agent_offline(vehicle_id, offline)

    def trigger_driver_non_compliance(self, vehicle_id: str = "V004"):
        """
        Simulates unexpected driver non-compliance on an agent.
        """
        agent = self.normal_agents.get(vehicle_id)
        if agent:
            agent.driver_profile["driver_compliance_label"] = "Low"
            agent.driver_compliance_probability = 0.05
            agent.is_compliant = False
            agent.response_timer_seconds = agent.max_yield_wait_time + 1.0
            agent._simulate_driver_response(dt=1.0)

    def get_monitoring_gateway_summary(self) -> Dict[str, Any]:
        """
        Provides aggregated read-only metrics for dashboard consumption.
        Does NOT centrally dictate vehicle movements.
        """
        normal_summaries = [a.get_public_summary() for a in self.normal_agents.values()]
        ev_summary = self.emergency_agent.get_public_summary() if self.emergency_agent else None

        yielding_count = sum(1 for a in self.normal_agents.values() if a.is_compliant)
        non_yielding_count = sum(1 for a in self.normal_agents.values() if a.failed_yielding_detected or not a.is_compliant)

        corridor_status = self.emergency_agent.corridor_status if self.emergency_agent else "INITIALIZING"
        active_route = self.emergency_agent.active_route if self.emergency_agent else {}
        replan_events = self.emergency_agent.replan_events if self.emergency_agent else []

        # DPSO recommended actions from agents
        recommended_actions = []
        for a in self.normal_agents.values():
            if a.current_recommendation:
                recommended_actions.append(a.current_recommendation)

        return {
            "total_agents": len(self.normal_agents) + (1 if self.emergency_agent else 0),
            "normal_agents_count": len(self.normal_agents),
            "emergency_vehicle": ev_summary,
            "corridor_status": corridor_status,
            "active_scenario": self.active_scenario,
            "yielding_count": yielding_count,
            "non_yielding_count": non_yielding_count,
            "active_route": active_route,
            "replan_events": replan_events,
            "recommended_actions": recommended_actions,
            "communication_stats": peer_network.get_communication_stats(),
            "normal_agents": normal_summaries
        }


# Singleton registry
agent_registry = VehicleAgentRegistry()

