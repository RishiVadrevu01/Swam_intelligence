from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.core.corridor_manager import corridor_manager
from app.core.scenario_generator import scenario_gen


router = APIRouter(prefix="/api/data", tags=["Data Management"])


class ScenarioRequest(BaseModel):
    scenario: str = "Scenario A: Normal Emergency Corridor"
    vehicle_count: int = 25
    seed: int = 42


@router.get("/vehicles")
def get_vehicles():
    return {
        "status": "success",
        "total": len(corridor_manager.vehicles),
        "data": corridor_manager.vehicles
    }


@router.get("/emergency-vehicles")
def get_emergency_vehicles():
    return {
        "status": "success",
        "data": [corridor_manager.emergency_vehicle] if corridor_manager.emergency_vehicle else []
    }


@router.get("/traffic")
def get_traffic():
    return {
        "status": "success",
        "total": len(corridor_manager.roads),
        "data": corridor_manager.roads
    }


@router.get("/roads")
def get_roads():
    return {
        "status": "success",
        "total": len(corridor_manager.roads),
        "data": corridor_manager.roads
    }


@router.post("/generate-scenario")
def generate_scenario(req: ScenarioRequest):
    result = corridor_manager.load_scenario(req.scenario, seed=req.seed)
    return {
        "status": "success",
        "message": f"Successfully activated {req.scenario}",
        "scenario": req.scenario,
        "corridor_status": result
    }

