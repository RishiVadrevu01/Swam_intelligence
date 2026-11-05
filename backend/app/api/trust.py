from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from app.core.corridor_manager import corridor_manager
from app.core.trust_engine import trust_engine


router = APIRouter(prefix="/api/trust", tags=["Trust & Anomaly Detection"])


class TrustEvaluationRequest(BaseModel):
    vehicle_id: str
    position_consistency: float = 0.90
    movement_consistency: float = 0.90
    message_freshness: float = 0.95
    sensor_consistency: float = 0.90
    weights_override: Dict[str, float] = None


@router.get("/vehicles")
def get_all_vehicle_trust():
    results = list(corridor_manager.trust_evaluations.values())
    return {
        "status": "success",
        "total": len(results),
        "data": results
    }


@router.get("/anomalies")
def get_anomalies_only():
    anomalies = [
        t for t in corridor_manager.trust_evaluations.values()
        if t.get("is_anomaly") or t.get("trust_category") == "Suspicious"
    ]
    return {
        "status": "success",
        "total_anomalies": len(anomalies),
        "data": anomalies
    }


@router.post("/evaluate")
def evaluate_custom_trust(req: TrustEvaluationRequest):
    vehicle = next((v for v in corridor_manager.vehicles if v["vehicle_id"] == req.vehicle_id), {
        "vehicle_id": req.vehicle_id,
        "speed": 45.0,
        "acceleration": 0.5,
        "heading": 48.0
    })
    trust_input = {
        "position_consistency": req.position_consistency,
        "movement_consistency": req.movement_consistency,
        "message_freshness": req.message_freshness,
        "sensor_consistency": req.sensor_consistency
    }
    result = trust_engine.evaluate_vehicle_trust(
        vehicle=vehicle,
        trust_info=trust_input,
        weights_override=req.weights_override
    )
    return {
        "status": "success",
        "data": result
    }

