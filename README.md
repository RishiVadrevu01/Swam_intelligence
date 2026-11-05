# Trust- and Compliance-Aware Decentralised Emergency Vehicle Corridor Coordination Using Local Digital Twins and Swarm Intelligence

A functional, full-stack, algorithm-driven web application demonstrating decentralised emergency vehicle corridor coordination across connected autonomous vehicle agents without relying on centralized bottlenecks or external traffic simulators.

---

## 1. System Overview

In urban arterial corridors, emergency vehicles (ambulances, fire engines) face delays due to congestion, unyielding drivers, and malicious or malfunctioning vehicles broadcasting false telemetry. 

This platform implements a **decentralised multi-agent architecture** where:
1. Every participating vehicle maintains an independent **Local Digital Twin (LDT)** representing its immediate spatio-temporal neighborhood.
2. Vehicles authenticate V2X packets using **ECDSA (NIST P-256) digital signatures**, SHA-256 integrity digests, and sequence replay detection.
3. Node reliability is assessed via a **multi-component Behavioural Trust Model** coupled with an **Isolation Forest anomaly detector**.
4. Future vehicle trajectories are predicted across multi-step horizons using a **PyTorch LSTM Seq2Seq Neural Network**.
5. Driver yielding propensities are inferred using an **XGBoost Classifier**.
6. Cooperative yielding maneuvers (lane transitions, speed reductions, headway reservations) are coordinated via **Distributed Particle Swarm Optimisation (DPSO)**.
7. Feasible routes and real-time reroutes around non-yielding blockages are solved using **A\* Graph Search with Dynamic Replanning**.

---

## 2. Architecture

```
React.js Dashboard (7 Interactive Pages)
   │
   ▼ REST API Calls (Axios)
FastAPI Backend (/api)
   │
   ├── Core Modules
   │    ├── Cryptography (ECDSA P-256 + SHA-256 + Replay Prevention)
   │    ├── Local Digital Twin Manager (Independent State per Node)
   │    ├── Behavioural Trust Engine: T(i) = w₁P + w₂C + w₃F + w₄S
   │    ├── Isolation Forest Kinematic Anomaly Detector
   │    ├── PyTorch LSTM Trajectory Predictor (5-step forecast)
   │    ├── XGBoost Driver Compliance Classifier (Yielding Propensity)
   │    ├── Distributed Particle Swarm Optimisation (DPSO Swarm Engine)
   │    ├── A* Graph Path Planner & Dynamic Replanner (NetworkX)
   │    └── Emergency Corridor Orchestrator (16-Step Lifecycle)
   │
   └── Synthetic Datasets & Generator (5 Realistic Scenarios A-E)
```

---

## 3. Core Modules (1 to 9)

### Module 1: Synthetic Data Management
- Realistic urban arterial grid in San Francisco (Market St corridor with 8 intersections and 10 road segments).
- 1 Emergency Ambulance (EV01) with priority 1 dispatch.
- 25-30 normal vehicles distributed across multiple lanes (Lane 1 Left, Lane 2 Center, Lane 3 Right).
- Multiple persistent JSON files: `vehicles.json`, `emergency_vehicles.json`, `traffic.json`, `roads.json`, `driver_behaviour.json`, `trust_data.json`, `communication.json`.
- Configurable scenario generation engine with reproducible random seed.

### Module 2: Secure V2X Communication & Authentication
- Asymmetric cryptography using Python's `cryptography` library.
- ECDSA digital signatures using SECP256R1 (NIST P-256) curve.
- SHA-256 canonical hashing of message content.
- Message freshness enforcement ($|t_{now} - t_{msg}| \le 15$s).
- Sequence number tracking to detect and reject replay attacks.

### Module 3: Local Digital Twin Management
- Each vehicle maintains an isolated onboard Local Digital Twin (`LocalDigitalTwin`).
- Tracks ego position, velocity, heading, and lane.
- Localized neighbor discovery within DSRC/C-V2X radio range ($<450$m).
- Integrates neighbor telemetry weighted by evaluated trust scores.
- Stale data detection and historical state snapshots.

### Module 4: Trust Evaluation & Anomaly Detection
- **Isolation Forest**: Unsupervised anomaly detection trained on speed, acceleration, displacement, angular deviation, broadcast frequency, and kinematic consistency.
- **Behavioural Trust Model**:
  $$T(i) = w_1 P(i) + w_2 C(i) + w_3 F(i) + w_4 S(i)$$
  where $w_1 = 0.35$ (Position Plausibility), $w_2 = 0.25$ (Movement Consistency), $w_3 = 0.20$ (Message Freshness), $w_4 = 0.20$ (Sensor Consistency).
- Penalizes anomalies and classifies vehicles into **High Trust** ($\ge 0.75$), **Medium Trust** ($0.45 - 0.75$), and **Suspicious / Quarantined** ($< 0.45$).

### Module 5: Vehicle Trajectory Prediction (LSTM)
- PyTorch 2-layer LSTM sequence-to-sequence neural network.
- Input: 5 historical timesteps of $[lat, lon, speed, accel, heading]$.
- Output: 5 future timesteps ($t+1$ to $t+5$ seconds ahead) with uncertainty radius estimation.

### Module 6: Driver Compliance Prediction (XGBoost)
- Trained multi-class XGBoost model evaluating:
  1. Distance from emergency vehicle
  2. Vehicle speed
  3. Lane position
  4. Available yielding space
  5. Time since emergency announcement
  6. Historical yielding actions
  7. Speed reduction readiness
  8. Lateral displacement history
  9. Driver response time
- Outputs yielding probability ($0.0 - 1.0$), compliance class (`High`, `Medium`, `Low`), and feature importances.

### Module 7: Decentralised Swarm Coordination (DPSO)
- Distributed Particle Swarm Optimisation where vehicles act as cooperative swarm particles.
- Action Space: `MOVE_LEFT`, `MOVE_RIGHT`, `REDUCE_SPEED`, `MAINTAIN_GAP`, `MAINTAIN_POSITION`.
- Multi-objective fitness minimization:
  $$\text{Fitness} = \alpha(\text{EmergencyDelay}) + \beta(\text{SafetyPenalty}) + \gamma(\text{TrafficDelay}) + \delta(\text{ConflictPenalty}) + \epsilon(\text{CompliancePenalty})$$
- Generates action directives, target speeds, safety headways, and conflict detection.

### Module 8: A* Route Planning & Dynamic Replanning
- NetworkX directed graph representation of the arterial network.
- A* Search with admissible Euclidean heuristic and dynamic edge weights incorporating length, congestion density, and non-yielding blockage penalties.
- Dynamic Replanning: Reroutes EV01 via alternate bypass (Mission St Bypass) when a non-compliant driver blocks the primary corridor.

### Module 9: Integrated 16-Step Corridor Lifecycle
1. Identify Emergency Vehicle (EV01)
2. Receive emergency broadcast announcement
3. Authenticate packet via ECDSA signature
4. Check message timestamp freshness and sequence replay
5. Update individual Local Digital Twins
6. Evaluate multi-component behavioural trust
7. Detect kinematic anomalies via Isolation Forest
8. Predict multi-step vehicle trajectories via LSTM
9. Predict driver yielding compliance via XGBoost
10. Execute decentralised DPSO swarm optimization
11. Compute feasible path using A* search
12. Dispatch recommended movement directives
13. Monitor synthetic vehicle behaviour
14. Detect failed yielding actions / obstructions
15. Trigger real-time dynamic replanning
16. Update and clear emergency corridor

---

## 4. Frontend Dashboard (7 Interactive Pages)

1. **Executive Dashboard**: KPI summary cards, emergency vehicle status, trust distribution chart (Recharts), compliance distribution chart, live event stream.
2. **Live Traffic Map**: React Leaflet interactive map with custom markers (Ambulance, Yielding, Suspicious, Non-yielding), road segment congestion polylines, active corridor highlight, vehicle filter bar, and inspection side panel.
3. **Local Digital Twin Explorer**: Vehicle selector to inspect any vehicle agent's onboard Local Digital Twin, localized neighbor perception table, trust attenuation, and snapshot history.
4. **Security & Trust Intelligence**: Cryptographic verification audit logs, registered public keys, Isolation Forest anomaly detections, and trust component breakdown ($P, C, F, S$).
5. **AI Prediction Centre**: PyTorch LSTM trajectory forecast (step coordinates & confidence) and XGBoost compliance predictions with Gini feature importance bar chart.
6. **Swarm Coordination Centre**: DPSO iteration vs. fitness convergence curve, objective penalty breakdown, recommended action table, and configurable swarm runner.
7. **Emergency Corridor Operations**: End-to-end corridor status, dynamic replanning simulator ("Simulate Driver Non-Compliance & Replan"), and before/after route comparison.

---

## 5. Synthetic Scenarios

- **Scenario A: Normal Emergency Corridor**: High driver compliance (~90%), low congestion, smooth center lane clearance.
- **Scenario B: Non-Cooperative Drivers**: Multiple stubborn drivers (V004, V008, V012) refuse to yield, triggering dynamic A* replanning.
- **Scenario C: Suspicious Vehicle Information**: Anomalous nodes inject false speeds, erratic heading swings, and corrupted signatures.
- **Scenario D: High Traffic Congestion**: Heavy vehicle density and reduced space along the arterial network.
- **Scenario E: Dynamic Traffic Conditions**: Evolving traffic states and real-time lane transitions.

---

## 6. Installation & Execution Guide

### Prerequisites
- Python 3.11+
- Node.js v18+ and npm

### Backend Setup

1. Open a terminal in the project root:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Re-train ML models (models are already trained and saved in `backend/app/ml/saved_models/`):
   ```bash
   python -m app.ml.train_trajectory
   python -m app.ml.train_compliance
   ```

4. Run the automated test suite:
   ```bash
   pytest tests/test_api.py -v
   ```

5. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   API Documentation is accessible at `http://127.0.0.1:8000/docs`.

### Frontend Setup

1. Open a second terminal in the project root:
   ```bash
   cd frontend
   ```

2. Install dependencies (if not already installed):
   ```bash
   npm install
   ```

3. Build for production or start the Vite development server:
   ```bash
   # Development Server
   npm run dev

   # Production Build
   npm run build
   ```

4. Open `http://localhost:5173` in your browser.

---

## 7. Verification Test Results

All 9 automated unit and integration tests execute successfully:
- `test_root_and_health`: PASSED
- `test_dashboard_summary`: PASSED
- `test_data_endpoints`: PASSED
- `test_v2x_security`: PASSED (ECDSA P-256 verified, corrupted signature rejected)
- `test_digital_twins`: PASSED (Independent LDT state verified)
- `test_trust_and_anomalies`: PASSED (Isolation Forest & Behavioural Trust verified)
- `test_ai_predictions`: PASSED (PyTorch LSTM & XGBoost models verified)
- `test_swarm_dpso_coordination`: PASSED (Multi-objective DPSO swarm optimization verified)
- `test_dynamic_replanning`: PASSED (A* dynamic rerouting verified)

