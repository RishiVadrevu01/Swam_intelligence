import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.data import router as data_router
from app.api.security import router as security_router
from app.api.digital_twins import router as digital_twins_router
from app.api.trust import router as trust_router
from app.api.prediction import router as prediction_router
from app.api.routing import router as routing_router
from app.api.coordination import router as coordination_router
from app.api.corridor import router as corridor_router
from app.api.dashboard import router as dashboard_router
from app.api.evaluation import router as evaluation_router
from app.api.agents import router as agents_router
from app.core.corridor_manager import corridor_manager
from app.vehicle_agents.agent_registry import agent_registry


app = FastAPI(
    title="Trust & Compliance-Aware Emergency Corridor Coordination API",
    description="Decentralised Emergency Vehicle Corridor Coordination using Local Digital Twins and Swarm Intelligence (DPSO)",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API Routers
app.include_router(dashboard_router)
app.include_router(data_router)
app.include_router(security_router)
app.include_router(digital_twins_router)
app.include_router(trust_router)
app.include_router(prediction_router)
app.include_router(routing_router)
app.include_router(coordination_router)
app.include_router(corridor_router)
app.include_router(evaluation_router)
app.include_router(agents_router)


@app.on_event("startup")
def startup_event():
    print("Initializing Emergency Vehicle Corridor Coordination Backend...")
    # Initialize decentralized multi-agent registry
    try:
        agent_registry.initialize_from_scenario("Scenario A: Normal Traffic")
        print(f"Decentralized agent fleet initialized ({len(agent_registry.normal_agents)} normal + 1 emergency agent).")
    except Exception as e:
        print(f"Warning initializing agent registry: {e}")

    # Trigger initial cycle if not already run
    if not corridor_manager.dpso_results:
        corridor_manager.execute_coordination_cycle()
    print("Backend initialization complete. Ready to serve requests.")


@app.get("/")
def root():
    return {
        "system": "Trust- and Compliance-Aware Emergency Corridor Coordination Platform",
        "version": "1.0.0",
        "status": "ONLINE",
        "active_corridor": corridor_manager.corridor_status,
        "docs_url": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "emergency-corridor-backend"}

