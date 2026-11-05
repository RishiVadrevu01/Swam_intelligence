from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.core.corridor_manager import corridor_manager


router = APIRouter(prefix="/api/corridor", tags=["Emergency Corridor Management"])


class ReplanTriggerRequest(BaseModel):
    vehicle_id: Optional[str] = None


@router.post("/initialize")
def initialize_corridor():
    status = corridor_manager.execute_coordination_cycle()
    return {
        "status": "success",
        "message": "Emergency corridor coordination cycle initiated",
        "data": status
    }


@router.post("/update")
def update_corridor():
    status = corridor_manager.execute_coordination_cycle()
    return {
        "status": "success",
        "message": "Emergency corridor refreshed",
        "data": status
    }


@router.post("/replan")
def trigger_corridor_replan(req: ReplanTriggerRequest):
    status = corridor_manager.simulate_failed_yielding_and_replan(vehicle_id=req.vehicle_id)
    return {
        "status": "success",
        "message": "Corridor dynamic replan executed",
        "data": status
    }


@router.get("/status")
def get_corridor_status():
    return {
        "status": "success",
        "data": corridor_manager.get_corridor_status()
    }

