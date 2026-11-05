from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from app.core.digital_twin_manager import digital_twin_manager


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
    twins = digital_twin_manager.get_all_twins_summary()
    return {
        "status": "success",
        "total": len(twins),
        "data": twins
    }


@router.get("/{vehicle_id}")
def get_digital_twin_by_id(vehicle_id: str):
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

