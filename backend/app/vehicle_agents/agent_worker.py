import argparse
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.vehicle_agents.normal_vehicle_agent import NormalVehicleAgent
from app.vehicle_agents.emergency_vehicle_agent import EmergencyVehicleAgent
from app.vehicle_agents.communication.message_protocol import V2XMessagePayload


def create_agent_app(vehicle_id: str, is_emergency: bool = False, initial_data: Optional[Dict[str, Any]] = None) -> FastAPI:
    """
    Creates an independent OBU microservice app for a single vehicle agent.
    """
    app = FastAPI(
        title=f"OBU Microservice - {vehicle_id}",
        description=f"Independent On-Board Unit execution for vehicle {vehicle_id}"
    )

    # Initialize agent
    if is_emergency:
        data = initial_data or {
            "emergency_vehicle_id": vehicle_id,
            "latitude": 17.385044,
            "longitude": 78.486671,
            "speed": 16.5,
            "heading": 90.0,
            "current_lane": 1,
            "vehicle_type": "Ambulance",
            "priority_level": "CRITICAL",
            "emergency_status": "ACTIVE"
        }
        agent = EmergencyVehicleAgent(vehicle_id=vehicle_id, initial_data=data)
    else:
        data = initial_data or {
            "vehicle_id": vehicle_id,
            "latitude": 17.385500,
            "longitude": 78.487000,
            "speed": 12.0,
            "acceleration": 0.0,
            "heading": 90.0,
            "current_lane": 1,
            "vehicle_type": "Car",
            "movement_direction": "East"
        }
        agent = NormalVehicleAgent(vehicle_id=vehicle_id, initial_data=data)

    is_offline = False

    @app.get("/health")
    def health():
        return {
            "status": "offline" if is_offline else "online",
            "vehicle_id": vehicle_id,
            "is_emergency": is_emergency,
            "public_key_pem": agent.identity.public_key_pem
        }

    @app.get("/state")
    def get_state():
        if is_offline:
            raise HTTPException(status_code=503, detail="Agent OBU is offline")
        return agent.get_monitoring_summary()

    @app.get("/digital-twin")
    def get_digital_twin():
        if is_offline:
            raise HTTPException(status_code=503, detail="Agent OBU is offline")
        return agent.digital_twin.to_dict()

    class StepRequest(BaseModel):
        dt: float = 1.0

    @app.post("/step")
    def step_agent(req: StepRequest):
        if is_offline:
            return {"status": "skipped", "reason": "agent_offline"}
        beacon = agent.step(req.dt)
        return {
            "status": "success",
            "step": agent.local_step_count,
            "beacon": beacon.model_dump() if beacon else None,
            "summary": agent.get_monitoring_summary()
        }

    @app.post("/v2v/receive")
    def receive_v2v_message(message: V2XMessagePayload):
        if is_offline:
            return {"status": "dropped", "reason": "agent_offline"}
        accepted = agent.receive_message(message)
        return {"status": "processed", "accepted": accepted}

    class FaultRequest(BaseModel):
        offline: bool

    @app.post("/fault")
    def set_fault(req: FaultRequest):
        nonlocal is_offline
        is_offline = req.offline
        return {"vehicle_id": vehicle_id, "is_offline": is_offline}

    return app


def main():
    parser = argparse.ArgumentParser(description="Run an independent vehicle OBU microservice.")
    parser.add_argument("--id", type=str, required=True, help="Unique vehicle ID (e.g. V001 or EV01)")
    parser.add_argument("--port", type=int, required=True, help="Port to bind to (e.g. 8001)")
    parser.add_argument("--emergency", action="store_true", help="Flag if this vehicle is an emergency vehicle")
    args = parser.parse_args()

    app = create_agent_app(vehicle_id=args.id, is_emergency=args.emergency)
    print(f"Starting Independent Vehicle OBU microservice for {args.id} on port {args.port}...")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":
    main()

