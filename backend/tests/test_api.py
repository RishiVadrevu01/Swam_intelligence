import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)


def test_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "ONLINE"

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"


def test_dashboard_summary():
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "charts" in data
    assert data["kpis"]["total_vehicles"] >= 20
    assert data["kpis"]["active_emergency_vehicles"] == 1


def test_data_endpoints():
    v_res = client.get("/api/data/vehicles")
    assert v_res.status_code == 200
    assert len(v_res.json()["data"]) >= 20

    ev_res = client.get("/api/data/emergency-vehicles")
    assert ev_res.status_code == 200
    assert len(ev_res.json()["data"]) == 1

    r_res = client.get("/api/data/roads")
    assert r_res.status_code == 200
    assert len(r_res.json()["data"]) >= 5


def test_v2x_security():
    # 1. Sign message
    sign_res = client.post("/api/security/sign-message", json={
        "vehicle_id": "V001",
        "message_type": "TELEMETRY_BEACON",
        "sequence_number": 999,
        "message_content": {"speed": 45.0, "lane": 2}
    })
    assert sign_res.status_code == 200
    signed_msg = sign_res.json()["signed_message"]
    assert signed_msg["signature_status"] == "SIGNED"
    assert "signature_hex" in signed_msg

    # 2. Verify legitimate message
    verify_res = client.post("/api/security/verify-message", json={"message": signed_msg})
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is True

    # 3. Verify corrupted signature rejected
    corrupted = dict(signed_msg)
    corrupted["signature_hex"] = "badc0ffee" * 4
    bad_verify = client.post("/api/security/verify-message", json={"message": corrupted})
    assert bad_verify.status_code == 200
    assert bad_verify.json()["is_valid"] is False


def test_digital_twins():
    twins_res = client.get("/api/digital-twins")
    assert twins_res.status_code == 200
    twins = twins_res.json()["data"]
    assert len(twins) >= 20

    single_res = client.get("/api/digital-twins/V001")
    assert single_res.status_code == 200
    v1_twin = single_res.json()["data"]
    assert v1_twin["vehicle_id"] == "V001"
    assert "own_position" in v1_twin
    assert "nearby_vehicles" in v1_twin


def test_trust_and_anomalies():
    trust_res = client.get("/api/trust/vehicles")
    assert trust_res.status_code == 200
    records = trust_res.json()["data"]
    assert len(records) >= 20

    anom_res = client.get("/api/trust/anomalies")
    assert anom_res.status_code == 200


def test_ai_predictions():
    # Trajectory prediction with LSTM
    traj_res = client.post("/api/prediction/trajectory", json={"vehicle_id": "V001", "steps": 5})
    assert traj_res.status_code == 200
    traj_data = traj_res.json()["data"]
    assert traj_data["model_used"] == "PyTorch-LSTM-Seq2Seq"
    assert len(traj_data["predicted_points"]) == 5

    # Driver compliance prediction with XGBoost
    comp_res = client.post("/api/prediction/compliance", json={
        "vehicle_id": "V001",
        "distance_from_ev": 100.0,
        "vehicle_speed": 40.0,
        "lane_position": 2,
        "available_space": 70.0,
        "previous_yielding_actions": 6,
        "response_time": 2.2
    })
    assert comp_res.status_code == 200
    comp_data = comp_res.json()["data"]
    assert "yielding_probability" in comp_data
    assert comp_data["compliance_class"] in ["High", "Medium", "Low"]


def test_swarm_dpso_coordination():
    dpso_res = client.post("/api/coordination/execute", json={"num_particles": 15, "max_iterations": 10})
    assert dpso_res.status_code == 200
    data = dpso_res.json()["data"]
    assert "convergence_history" in data
    assert len(data["convergence_history"]) == 10
    assert len(data["recommended_actions"]) > 0


def test_dynamic_replanning():
    replan_res = client.post("/api/routing/replan", json={"failed_vehicle_id": "V004", "blocked_road_id": "ROAD_02"})
    assert replan_res.status_code == 200
    status = replan_res.json()["corridor_status"]
    assert status["status"] == "REPLANNING"
    assert status["replan_data"] is not None

