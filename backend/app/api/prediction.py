from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from app.core.corridor_manager import corridor_manager
from app.core.trajectory_predictor import trajectory_predictor
from app.core.compliance_predictor import compliance_predictor


router = APIRouter(prefix="/api/prediction", tags=["AI Predictions (LSTM & XGBoost)"])


class TrajectoryRequest(BaseModel):
    vehicle_id: str
    steps: int = 5


class ComplianceRequest(BaseModel):
    vehicle_id: str
    distance_from_ev: float = 120.0
    vehicle_speed: float = 45.0
    lane_position: int = 2
    available_space: float = 60.0
    previous_yielding_actions: int = 5
    response_time: float = 2.4


@router.get("/results")
def get_prediction_results():
    return {
        "status": "success",
        "compliance_predictions": corridor_manager.compliance_predictions,
        "trajectory_predictions": corridor_manager.trajectory_predictions,
        "feature_importances": compliance_predictor.feature_importances
    }


@router.post("/trajectory")
def predict_vehicle_trajectory(req: TrajectoryRequest):
    vehicle = next((v for v in corridor_manager.vehicles if v["vehicle_id"] == req.vehicle_id), None)
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Vehicle {req.vehicle_id} not found")
    result = trajectory_predictor.predict_trajectory(vehicle, steps=req.steps)
    return {
        "status": "success",
        "data": result
    }


@router.post("/compliance")
def predict_driver_compliance(req: ComplianceRequest):
    vehicle = {
        "vehicle_id": req.vehicle_id,
        "speed": req.vehicle_speed,
        "current_lane": req.lane_position
    }
    behaviour = {
        "previous_yielding_actions": req.previous_yielding_actions,
        "response_time": req.response_time,
        "acceleration_history": [-0.5, -0.8]
    }
    result = compliance_predictor.predict_compliance(
        vehicle=vehicle,
        behaviour=behaviour,
        ev_distance=req.distance_from_ev,
        available_space=req.available_space
    )
    return {
        "status": "success",
        "data": result
    }

