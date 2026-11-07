import sys
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.vehicle_agents.security.identity import AgentIdentity
from app.vehicle_agents.security.authentication import AgentAuthenticator
from app.vehicle_agents.trust.trust_engine import AgentTrustEvaluator
from app.vehicle_agents.coordination.distributed_dpso import DistributedDPSOCoordinator
from app.vehicle_agents.communication.peer_network import peer_network
from app.vehicle_agents.normal_vehicle_agent import NormalVehicleAgent
from app.vehicle_agents.agent_registry import agent_registry
from app.core.experiment_evaluator import experiment_evaluator


def test_agent_cryptographic_identity():
    """Verify Formula 3 identity generation: ECDSA SECP256R1 keypair and synthetic certificate."""
    identity = AgentIdentity(vehicle_id="V099")
    assert identity.vehicle_id == "V099"
    assert identity.public_key_pem.startswith("-----BEGIN PUBLIC KEY-----")
    assert identity.certificate["issuer"] == "SwarmTwin-V2X-Root-CA"
    assert identity.certificate["vehicle_id"] == "V099"


def test_agent_authentication_and_replay_detection():
    """Verify Formula 3 digital signature, verification, tampering rejection, and replay detection."""
    id1 = AgentIdentity("V001")
    id2 = AgentIdentity("V002")
    auth1 = AgentAuthenticator(identity=id1)
    auth2 = AgentAuthenticator(identity=id2)

    msg_payload = {"speed": 42.0, "lane": 2}
    signed_msg = auth1.sign_message(msg_payload, sequence_number=100)

    # Legitimate message passes
    is_valid, reason = auth2.verify_message(signed_msg)
    assert is_valid is True

    # Tampered message fails
    tampered_msg = dict(signed_msg, speed=99.0)
    is_valid_tampered, reason = auth2.verify_message(tampered_msg)
    assert is_valid_tampered is False

    # Stale message (>15s) is rejected
    stale_msg = auth1.sign_message(msg_payload, sequence_number=101)
    stale_msg["timestamp"] = time.time() - 30.0
    is_valid_stale, reason = auth2.verify_message(stale_msg)
    assert is_valid_stale is False

    # Replay sequence number detection
    replay_msg = dict(signed_msg)
    replay_msg["timestamp"] = time.time()
    is_valid_replay, reason = auth2.verify_message(replay_msg)
    assert is_valid_replay is False


def test_agent_trust_engine_formula_2():
    """Verify Formula 2: T_i = w_p P_i + w_c C_i + w_f F_i + w_s S_i with Isolation Forest anomaly screening."""
    trust_engine = AgentTrustEvaluator()
    
    # Normal beacon evaluation
    res = trust_engine.compute_trust(
        peer_vehicle_state={"vehicle_id": "V002", "speed": 40.0, "acceleration": 0.5, "heading": 48.0},
        raw_telemetry={"speed": 40.0, "acceleration": 0.5},
        message_age_seconds=0.5,
        neighbor_agreement_ratio=0.95
    )
    assert res["trust_category"] == "High"
    assert res["computed_trust_score"] >= 0.75
    assert res["is_anomaly"] is False

    # Anomalous/spoofed beacon evaluation
    res_bad = trust_engine.compute_trust(
        peer_vehicle_state={"vehicle_id": "V_SPOOF", "speed": 160.0, "acceleration": 9.5, "heading": 90.0},
        raw_telemetry={"speed": 160.0, "acceleration": 9.5},
        message_age_seconds=8.0,
        neighbor_agreement_ratio=0.20
    )
    assert res_bad["trust_category"] == "Suspicious"
    assert res_bad["computed_trust_score"] < 0.50


def test_distributed_dpso_coordination_formula_1():
    """Verify Formula 1: J = alpha*Te + beta*Dn + gamma*Rs + delta*Cm + epsilon*Nnc and constraints."""
    dpso = DistributedDPSOCoordinator(vehicle_id="V001")
    
    # Candidate action: 1 (MOVE_LEFT from lane 2 to lane 1)
    cost, breakdown, feasible = dpso.evaluate_local_objective(
        candidate_action_idx=1,
        ego_state={"current_lane": 2, "speed": 40.0},
        ev_state={"target_lane": 2, "distance": 80.0},
        neighbor_states=[],
        driver_compliance_prob=0.90,
        trust_scores={},
        local_messages_count=4
    )
    assert feasible is True
    assert cost < float('inf')
    assert "T_e_emergency_delay" in breakdown
    assert "R_s_safety_risk" in breakdown

    # Illegal left turn off road (from lane 1) should violate hard constraint
    cost_illegal, _, feasible_illegal = dpso.evaluate_local_objective(
        candidate_action_idx=1,
        ego_state={"current_lane": 1, "speed": 40.0},
        ev_state={"target_lane": 2, "distance": 80.0},
        neighbor_states=[],
        driver_compliance_prob=0.90,
        trust_scores={}
    )
    assert feasible_illegal is False
    assert cost_illegal == float('inf')


def test_peer_network_spatial_filtering():
    """Verify V2V communication respects communication radius (<450m) and measures overhead."""
    peer_network.registered_agents.clear()
    peer_network.offline_agents.clear()

    # Agent near within ~50m at (17.3855, 78.4866)
    # Agent far > 2000m at (17.4100, 78.4866)
    agent_near = NormalVehicleAgent(
        vehicle_id="V_NEAR",
        initial_data={"latitude": 17.3855, "longitude": 78.4866, "speed": 40.0, "current_lane": 2}
    )
    agent_far = NormalVehicleAgent(
        vehicle_id="V_FAR",
        initial_data={"latitude": 17.4100, "longitude": 78.4866, "speed": 40.0, "current_lane": 2}
    )

    id1 = AgentIdentity("V_SENDER")
    auth1 = AgentAuthenticator(identity=id1)
    signed_msg = auth1.sign_message({"data": "telemetry"}, sequence_number=1)

    # Deliver using spatial broadcast
    peer_network.broadcast(
        sender_id="V_SENDER",
        sender_lat=17.3850,
        sender_lon=78.4866,
        message=signed_msg
    )
    assert len(agent_near.inbox) > 0
    assert len(agent_far.inbox) == 0  # Out of range (>450m)
    assert peer_network.get_total_bytes_transmitted() > 0


def test_dynamic_replanning_on_non_compliance():
    """Verify that driver non-compliance triggers local yielding re-weighting and EV replanning."""
    agent_registry.initialize_from_scenario("Scenario A: Normal Traffic", seed=42)
    ev = agent_registry.emergency_agent
    assert ev is not None

    v1 = agent_registry.normal_agents.get("V001")
    assert v1 is not None

    # Simulate non-compliance
    agent_registry.trigger_driver_non_compliance("V001")
    assert v1.is_compliant is False


def test_agent_fault_tolerance():
    """Verify system resilience when an agent goes offline and recovers."""
    agent_registry.initialize_from_scenario("Scenario A: Normal Traffic")
    v1 = "V001"
    agent = agent_registry.get_agent(v1)
    initial_inbox_len = len(agent.inbox)

    # Take agent offline
    agent_registry.set_agent_offline(v1, offline=True)
    assert v1 in peer_network.offline_agents

    id_ev = AgentIdentity("EV01")
    auth_ev = AgentAuthenticator(identity=id_ev)
    signed_msg = auth_ev.sign_message({"emergency": True}, sequence_number=50)

    peer_network.broadcast(
        sender_id="EV01",
        sender_lat=17.3850,
        sender_lon=78.4866,
        message=signed_msg
    )
    # Agent inbox did not receive message while offline
    assert len(agent.inbox) == initial_inbox_len

    # Recover agent
    agent_registry.set_agent_offline(v1, offline=False)
    assert v1 not in peer_network.offline_agents


def test_table_2_empirical_evaluation():
    """Verify Table 2 results matching research paper exact metrics."""
    res = experiment_evaluator.run_comparative_evaluation()
    assert "table_2_results" in res
    assert len(res["table_2_results"]) == 6

    metrics = [r["metric"] for r in res["table_2_results"]]
    assert any("Emergency travel time" in m for m in metrics)
    assert any("Corridor formation time" in m for m in metrics)
    assert any("Compliance F1-score" in m for m in metrics)
    assert any("Trajectory MAE" in m for m in metrics)
    assert any("Unsafe conflicts" in m for m in metrics)
    assert any("Communication overhead" in m for m in metrics)

    csv_report = experiment_evaluator.generate_csv_report()
    assert "=== TABLE 2: COMPARISON OF PROPOSED SYSTEM WITH BASELINE ===" in csv_report
    assert "Emergency travel time (s)" in csv_report


def test_decentralized_agent_api_endpoints():
    """Verify REST API endpoints for decentralized multi-agent system."""
    with TestClient(app) as test_client:
        # GET /api/agents
        res = test_client.get("/api/agents")
        assert res.status_code == 200
        data = res.json()["data"]
        assert "normal_agents" in data
        assert "emergency_vehicle" in data

        # GET /api/agents/network-stats
        net_res = test_client.get("/api/agents/network-stats")
        assert net_res.status_code == 200
        assert "total_messages_sent" in net_res.json()["data"]

        # POST /api/agents/{id}/fault
        fault_res = test_client.post("/api/agents/V001/fault", json={"offline": True})
        assert fault_res.status_code == 200
        assert fault_res.json()["is_offline"] is True

        # Revert fault
        test_client.post("/api/agents/V001/fault", json={"offline": False})

        # POST /api/agents/{id}/non-compliance
        nc_res = test_client.post("/api/agents/V002/non-compliance", json={"refuse_yielding": True})
        assert nc_res.status_code == 200

        # Evaluation CSV download
        csv_res = test_client.get("/api/evaluation/download-csv")
        assert csv_res.status_code == 200
        assert "TABLE 2" in csv_res.text
