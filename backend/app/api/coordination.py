from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from app.core.corridor_manager import corridor_manager
from app.core.dpso_engine import dpso_engine


router = APIRouter(prefix="/api/coordination", tags=["Swarm Coordination (DPSO)"])


class DPSOExecuteRequest(BaseModel):
    num_particles: int = 25
    max_iterations: int = 30
    alpha: float = 3.5
    beta: float = 4.0
    gamma: float = 1.5


@router.post("/execute")
def execute_coordination(req: DPSOExecuteRequest):
    cooperative_vehicles = [
        v for v in corridor_manager.vehicles
        if corridor_manager.trust_evaluations.get(v["vehicle_id"], {}).get("trust_category") != "Suspicious"
    ]
    compliance_map = {vid: comp["yielding_probability"] for vid, comp in corridor_manager.compliance_predictions.items()}
    trust_map = {vid: t["computed_trust_score"] for vid, t in corridor_manager.trust_evaluations.items()}

    custom_config = {
        "num_particles": req.num_particles,
        "max_iterations": req.max_iterations,
        "w": 0.65,
        "c1": 1.4,
        "c2": 1.6,
        "alpha": req.alpha,
        "beta": req.beta,
        "gamma": req.gamma,
        "delta": 3.0,
        "epsilon": 2.5
    }

    engine = dpso_engine.__class__(config=custom_config)
    results = engine.coordinate_vehicles(
        participating_vehicles=cooperative_vehicles,
        emergency_vehicle=corridor_manager.emergency_vehicle,
        compliance_map=compliance_map,
        trust_map=trust_map
    )
    corridor_manager.dpso_results = results

    return {
        "status": "success",
        "data": results
    }


@router.get("/results")
def get_coordination_results():
    if not corridor_manager.dpso_results:
        raise HTTPException(status_code=400, detail="No DPSO execution results found")
    return {
        "status": "success",
        "data": corridor_manager.dpso_results
    }


@router.get("/history")
def get_convergence_history():
    if not corridor_manager.dpso_results:
        return {"status": "success", "data": []}
    return {
        "status": "success",
        "convergence_history": corridor_manager.dpso_results.get("convergence_history", []),
        "best_fitness": corridor_manager.dpso_results.get("best_fitness"),
        "total_iterations": corridor_manager.dpso_results.get("total_iterations")
    }

