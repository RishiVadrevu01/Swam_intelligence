from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from app.core.digital_twin_manager import digital_twin_manager
from app.vehicle_agents.agent_registry import agent_registry


router = APIRouter(prefix="/api/digital-twins", tags=["Local Digital Twins"])


class TwinUpdateRequest(BaseModel):
    vehicle_id: str
    latitude: float
    longitude: float
    speed: float
    heading: float
    current_lane: int
    road_id: str


@router.get("")
def get_all_digital_twins():
    # If decentralized agents are active, return their twins summary
    if agent_registry.normal_agents:
        twins = []
        for vid, ag in agent_registry.normal_agents.items():
            twins.append({
                "vehicle_id": vid,
                "position": ag.digital_twin.own_position,
                "speed": ag.digital_twin.own_speed,
                "lane": ag.digital_twin.own_lane,
                "nearby_count": len(ag.digital_twin.nearby_vehicles),
                "is_stale": ag.digital_twin.is_stale,
                "last_update": ag.digital_twin.last_update_timestamp
            })
        if agent_registry.emergency_agent:
            ag = agent_registry.emergency_agent
            twins.insert(0, {
                "vehicle_id": ag.vehicle_id,
                "position": ag.digital_twin.own_position,
                "speed": ag.digital_twin.own_speed,
                "lane": ag.digital_twin.own_lane,
                "nearby_count": len(ag.digital_twin.nearby_vehicles),
                "is_stale": ag.digital_twin.is_stale,
                "last_update": ag.digital_twin.last_update_timestamp
            })
        return {
            "status": "success",
            "total": len(twins),
            "data": twins
        }

    twins = digital_twin_manager.get_all_twins_summary()
    return {
        "status": "success",
        "total": len(twins),
        "data": twins
    }


@router.get("/{vehicle_id}")
def get_digital_twin_by_id(vehicle_id: str):
    # Check decentralized agent registry first
    agent = agent_registry.get_agent(vehicle_id)
    if agent:
        agent.digital_twin.check_staleness()
        return {
            "status": "success",
            "vehicle_id": vehicle_id,
            "data": agent.digital_twin.to_dict()
        }

    twin = digital_twin_manager.get_twin(vehicle_id)
    if not twin:
        raise HTTPException(status_code=404, detail=f"Local Digital Twin for vehicle {vehicle_id} not found")
    twin.check_staleness()
    return {
        "status": "success",
        "vehicle_id": vehicle_id,
        "data": twin.to_dict()
    }


@router.post("/update")
def update_digital_twin(req: TwinUpdateRequest):
    twin = digital_twin_manager.get_twin(req.vehicle_id)
    if not twin:
        raise HTTPException(status_code=404, detail=f"Local Digital Twin for vehicle {req.vehicle_id} not found")
    twin.update_own_telemetry(
        lat=req.latitude,
        lon=req.longitude,
        speed=req.speed,
        heading=req.heading,
        lane=req.current_lane,
        road_id=req.road_id
    )
    return {
        "status": "success",
        "message": f"Updated telemetry for Local Digital Twin {req.vehicle_id}",
        "data": twin.to_dict()
    }

