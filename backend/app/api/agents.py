from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.vehicle_agents.agent_registry import agent_registry
from app.vehicle_agents.communication.peer_network import peer_network

router = APIRouter(prefix="/api/agents", tags=["Decentralized Vehicle Agents"])


class StepRequest(BaseModel):
    dt: float = 1.0


class FaultRequest(BaseModel):
    offline: bool


class NonComplianceRequest(BaseModel):
    refuse_yielding: bool = True


class ScenarioInitRequest(BaseModel):
    scenario_name: str = "Scenario A: Normal Traffic"
    seed: int = 42


@router.get("")
def list_all_agents():
    """
    Returns public monitoring state of all decentralized vehicle agents,
    including emergency vehicle and P2P communication stats.
    """
    return {
        "status": "success",
        "data": agent_registry.get_monitoring_gateway_summary()
    }


@router.get("/network-stats")
def get_network_statistics():
    """
    Returns decentralized P2P V2V network metrics (bytes transmitted, dropped, topology).
    """
    return {
        "status": "success",
        "data": peer_network.get_communication_stats()
    }


@router.get("/{vehicle_id}")
def get_agent_detail(vehicle_id: str):
    """
    Returns internal state of a specific vehicle agent, including its
    cryptographic identity, local digital twin, trust scores, and DPSO plan.
    """
    agent = agent_registry.get_agent(vehicle_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {vehicle_id} not found")

    return {
        "status": "success",
        "data": {
            "summary": agent.get_public_summary(),
            "digital_twin": agent.digital_twin.to_dict(),
            "public_key_pem": agent.identity.public_key_pem,
            "security_log": agent.authenticator.security_log[-20:],
            "dpso_candidate": agent.dpso_coordinator.get_public_candidate()
        }
    }


@router.post("/step")
def trigger_agent_step(req: StepRequest = StepRequest()):
    """
    Triggers an asynchronous step across all independent vehicle agents.
    Each agent independently broadcasts beacons, reads neighbor messages,
    updates its local digital twin, evaluates trust, and executes local DPSO.
    """
    agent_registry.step_all(dt=req.dt)
    return {
        "status": "success",
        "step": agent_registry.current_step,
        "active_agents": len(agent_registry.normal_agents) + (1 if agent_registry.emergency_agent else 0)
    }


@router.post("/initialize")
def initialize_scenario(req: ScenarioInitRequest):
    """
    Re-initializes all decentralized agents for a specified scenario.
    """
    agent_registry.initialize_from_scenario(scenario_name=req.scenario_name, seed=req.seed)
    return {
        "status": "success",
        "scenario": req.scenario_name,
        "agents_count": len(agent_registry.normal_agents) + (1 if agent_registry.emergency_agent else 0)
    }


@router.post("/{vehicle_id}/fault")
def toggle_agent_fault(vehicle_id: str, req: FaultRequest):
    """
    Toggles an agent offline or online to test decentralization resilience and fault tolerance.
    """
    agent = agent_registry.get_agent(vehicle_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {vehicle_id} not found")

    agent_registry.set_agent_offline(vehicle_id, req.offline)
    return {
        "status": "success",
        "vehicle_id": vehicle_id,
        "is_offline": req.offline
    }


@router.post("/{vehicle_id}/non-compliance")
def trigger_agent_non_compliance(vehicle_id: str, req: NonComplianceRequest):
    """
    Simulates a stubborn driver event on a specific vehicle agent,
    triggering local DPSO re-weighting and dynamic A* replanning.
    """
    agent = agent_registry.normal_agents.get(vehicle_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Normal vehicle agent {vehicle_id} not found")

    agent_registry.trigger_driver_non_compliance(vehicle_id)
    return {
        "status": "success",
        "vehicle_id": vehicle_id,
        "is_compliant": agent.is_compliant,
        "failed_yielding_detected": agent.failed_yielding_detected
    }

