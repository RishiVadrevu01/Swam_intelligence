from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from app.core.corridor_manager import corridor_manager
from app.core.astar_router import astar_router


router = APIRouter(prefix="/api/routing", tags=["A* Routing & Dynamic Replanning"])


class RoutePlanRequest(BaseModel):
    start_node: str = "INT_1"
    destination_node: str = "INT_5"
    blocked_roads: List[str] = []


class RouteReplanRequest(BaseModel):
    failed_vehicle_id: str = "V004"
    blocked_road_id: str = "ROAD_02"


@router.post("/plan")
def plan_route(req: RoutePlanRequest):
    route = astar_router.find_route(
        start_node=req.start_node,
        destination_node=req.destination_node,
        blocked_roads=req.blocked_roads
    )
    return {
        "status": "success",
        "data": route
    }


@router.post("/replan")
def trigger_dynamic_replan(req: RouteReplanRequest):
    result = corridor_manager.simulate_failed_yielding_and_replan(vehicle_id=req.failed_vehicle_id)
    return {
        "status": "success",
        "message": f"Dynamic replanning triggered for failed yielding vehicle {req.failed_vehicle_id}",
        "corridor_status": result
    }

