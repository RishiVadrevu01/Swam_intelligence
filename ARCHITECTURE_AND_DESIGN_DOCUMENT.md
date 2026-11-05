# Trust- and Compliance-Aware Decentralised Emergency Vehicle Corridor Coordination Using Local Digital Twins and Swarm Intelligence

## Comprehensive System Architecture & UML Design Specification Document
*(Derived & Enhanced from `Traffic_review2.pptx`)*

**Project Team Members:**
- V Krishna Teja (23P61A66H6)
- V Manasa (23P61A66H9)
- S Sri Ram (23P61A66F4)

**Internal Guide:**
- Mrs. T. Adarana (Assistant Professor, Dept. of Computer Science & Engineering)

---

## Executive Summary

This specification document formalizes the software design, system architecture, and UML modeling for the **Trust- and Compliance-Aware Decentralised Emergency Vehicle Corridor Coordination Framework**.

Deriving foundational concepts from the review presentation **`Traffic_review2.pptx` (SwarmTwin)**, this implementation elevates the architecture into a fully autonomous, algorithm-driven application using **FastAPI**, **React.js**, and **synthetic JSON traffic telemetry**. It eliminates external traffic simulators (SUMO/TraCI/CARLA) and provides a pure software-driven decentralised coordination platform incorporating:
1. **ECDSA (NIST P-256) Digital Signatures & Replay Prevention**
2. **Independent Local Digital Twins (LDT)** on every vehicle agent
3. **Behavioural Trust Scoring & Isolation Forest Anomaly Detection**
4. **PyTorch LSTM Multi-Step Trajectory Prediction**
5. **XGBoost Driver Yielding Compliance Inference**
6. **Distributed Particle Swarm Optimization (DPSO)** for cooperative corridor establishment
7. **NetworkX A\* Graph Search with Real-Time Dynamic Replanning**

---

## 1. System Architecture Diagram
*(Referenced from Slide 8: System Architecture)*

### Diagram
```mermaid
flowchart TD
    subgraph SENSORS_LAYER["Vehicle & Sensor Layer"]
        subgraph V_OBU["Normal Vehicle (OBU)"]
            NV_SENS["On-board Telemetry (GPS, IMU, Speed, Heading, Lane)"]
            NV_V2X["V2X Cryptographic Client (ECDSA P-256)"]
        end

        subgraph EV_OBU["Ambulance (Priority Vehicle EV01)"]
            EV_SENS["Emergency Dispatch Telemetry (GPS, Speed, Heading)"]
            EV_SIG["Emergency Siren Broadcast & Priority Signal"]
        end

        subgraph AUTH_EXT["Traffic Authority & Infrastructure"]
            MAP_INC["Road Network Geometry (OSM, Intersections, Segments)"]
            CONG_DAT["Traffic Density & Capacity Constraints"]
        end
    end

    subgraph COMM_LAYER["V2X Communication Fabric"]
        V2X_BUS["Secure V2V / V2I Communication (ECDSA Signature Verification, SHA-256 Digest, Replay Defense)"]
    end

    NV_SENS --> NV_V2X
    EV_SENS --> EV_SIG
    NV_V2X --> V2X_BUS
    EV_SIG --> V2X_BUS
    MAP_INC --> V2X_BUS
    CONG_DAT --> V2X_BUS

    subgraph BACKEND_SERVER["Backend Processing Modules (FastAPI / Edge Engine)"]
        subgraph LDT_MODULE["Local Digital Twin (LDT) Engine"]
            DT_CORE["Independent Local Digital Twins per Vehicle"]
            DT_NEIGHBOR["Spatial Neighbor Discovery (<450m) & Staleness Pruning"]
        end

        subgraph TRUST_ANOMALY["Trust & Anomaly Detection Module"]
            ISO_FOREST["Isolation Forest (Kinematic Anomaly Detector)"]
            BEHAV_TRUST["Behavioural Trust Model: T = w1*P + w2*C + w3*F + w4*S"]
        end

        subgraph AI_PREDICTION["AI Prediction Centre"]
            LSTM_TRAJ["PyTorch LSTM Seq2Seq Trajectory Predictor (5-step horizon)"]
            XGB_COMP["XGBoost Driver Compliance Classifier (Yielding Propensity)"]
        end

        subgraph SWARM_DPSO["Swarm Intelligence Module (DPSO)"]
            DPSO_CORE["Distributed Particle Swarm Optimization"]
            DPSO_FIT["Multi-Objective Fitness Evaluator (Delay, Headway, Safety, Conflicts)"]
        end

        subgraph ROUTE_MODULE["Routing & Dynamic Replanning Module"]
            ASTAR_CORE["NetworkX A* Graph Search Engine"]
            REPLAN_ENG["Dynamic Bypass Replanner (Non-Compliance Rerouting)"]
        end
    end

    V2X_BUS --> LDT_MODULE
    V2X_BUS --> TRUST_ANOMALY
    LDT_MODULE --> AI_PREDICTION
    TRUST_ANOMALY --> LDT_MODULE
    TRUST_ANOMALY --> SWARM_DPSO
    AI_PREDICTION --> SWARM_DPSO
    SWARM_DPSO --> ROUTE_MODULE

    subgraph DATA_STORAGE["Synthetic Data & Storage Layer"]
        JSON_STORE[("JSON Scenario Datasets (Vehicles, Roads, Driver Behaviour, Trust, V2X Beacons)")]
        SAVED_MODELS[("Trained Model Weights (trajectory_lstm.pt, compliance_xgb.joblib)")]
    end

    JSON_STORE <--> BACKEND_SERVER
    SAVED_MODELS <--> AI_PREDICTION

    subgraph DASHBOARD_LAYER["Frontend Dashboard & In-Vehicle Display (React.js)"]
        UI_MAP["Live Leaflet Traffic Map with Corridor Overlay"]
        UI_TWIN["Local Digital Twin Inspector"]
        UI_SWARM["DPSO Swarm Convergence & Recommendations"]
        UI_SEC["V2X Cryptographic & Trust Intelligence Audit"]
        UI_REPLAN["Dynamic Replanning & Non-Compliance Simulator"]
    end

    BACKEND_SERVER <-->|REST APIs / WebSocket| DASHBOARD_LAYER
    DASHBOARD_LAYER --> DRIVER["Driver & Emergency Operator"]
```

### Architectural Description
1. **On-Board Units (OBU) & Sensor Layer**: Captures vehicle kinematics (speed, acceleration, heading, lane position). The ambulance (EV01) broadcasts priority dispatch intents.
2. **Secure V2X Fabric**: Applies ECDSA (SECP256R1) signing and SHA-256 hashing. Enforces timestamp validity ($|t_{now} - t_{msg}| \le 15$s) and monotonic sequence number checks to defeat replay attacks.
3. **Local Digital Twin (LDT) Engine**: Each vehicle agent maintains an isolated digital twin instance representing its local spatio-temporal neighborhood ($<450$m), incorporating trust-attenuated neighbor states.
4. **Trust & Anomaly Detection**:
   - **Isolation Forest**: Evaluates kinematics and flags sudden teleportations, impossible accelerations, and beacon flood anomalies.
   - **Behavioural Trust Model**: Evaluates $T(i) = 0.35P + 0.25C + 0.20F + 0.20S$ ($P$: position plausibility, $C$: movement consistency, $F$: message freshness, $S$: sensor consistency).
5. **AI Prediction Centre**:
   - **PyTorch LSTM**: Seq2Seq model forecasting 5 future timesteps ($t+1$ to $t+5$ seconds ahead) with uncertainty bounds.
   - **XGBoost Classifier**: Multi-class model predicting yielding probability ($0.0 - 1.0$) and compliance category (`High`, `Medium`, `Low`).
6. **Distributed PSO Swarm Optimization**: Multi-objective fitness function minimizing emergency delay, safety headway violations, normal traffic disruption, and trajectory conflicts. Dispatches actions: `MOVE_LEFT`, `MOVE_RIGHT`, `REDUCE_SPEED`, `MAINTAIN_GAP`, `MAINTAIN_POSITION`.
7. **A\* Route Planning & Dynamic Replanning**: NetworkX road graph with dynamic edge costs. If a vehicle fails to yield, edge blockage penalty ($+9999$) is triggered and the emergency route dynamically reroutes via the Mission Bypass.

---

## 2. Use Case Diagram
*(Referenced from Slide 11: Use Case Diagram)*

### Diagram
```mermaid
flowchart LR
    V_ACTOR["Normal Vehicle Agent"]:::actorStyle
    A_ACTOR["Ambulance (Priority Vehicle)"]:::actorStyle
    D_ACTOR["Driver / In-Vehicle UI"]:::actorStyle
    TA_ACTOR["Traffic Authority / Dispatcher"]:::actorStyle

    subgraph SYSTEM_BOUNDARY["Decentralised Emergency Corridor System"]
        UC1(["Collect & Sign Telemetry Data"])
        UC2(["Broadcast V2V State Beacons"])
        UC3(["Verify Cryptographic Signatures & Replay"])
        UC4(["Evaluate Behavioural Trust & Detect Anomalies"])
        UC5(["Send Emergency Dispatch Announcement"])
        UC6(["Update Local Digital Twins (LDT)"])
        UC7(["Predict Vehicle Trajectories (LSTM)"])
        UC8(["Predict Driver Yielding Compliance (XGBoost)"])
        UC9(["Execute Distributed PSO Swarm Coordination"])
        UC10(["Calculate Optimal Emergency Path (A*)"])
        UC11(["Detect Non-Yielding Obstruction"])
        UC12(["Trigger Dynamic Corridor Replanning"])
        UC13(["Provide Lateral/Speed Yield Directives"])
        UC14(["View Real-Time Traffic & Corridor Map"])
        UC15(["Inspect Local Digital Twin State"])
        UC16(["Provide Road Network & Incident Data"])
    end

    V_ACTOR --> UC1
    V_ACTOR --> UC2
    V_ACTOR --> UC3

    A_ACTOR --> UC5
    A_ACTOR --> UC10

    UC1 -.->|include| UC2
    UC2 -.->|include| UC3
    UC3 -.->|include| UC4
    UC5 -.->|include| UC6
    UC4 -.->|include| UC6
    UC6 -.->|include| UC7
    UC6 -.->|include| UC8
    UC7 -.->|include| UC9
    UC8 -.->|include| UC9
    UC9 -.->|include| UC13
    UC9 -.->|include| UC10

    UC11 -.->|include| UC12
    UC12 -.->|extend| UC10
    UC12 -.->|extend| UC9

    UC13 --> D_ACTOR
    UC14 --> D_ACTOR
    UC15 --> D_ACTOR

    TA_ACTOR --> UC16
    UC16 -.->|include| UC6
    TA_ACTOR --> UC14

    classDef actorStyle fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
```

### Actors and Use Case Details
- **Normal Vehicle Agent**: Collects kinematic telemetry, signs V2V beacons via ECDSA, detects neighbors, and verifies incoming packets.
- **Ambulance (Priority Vehicle)**: Broadcasts priority dispatch signal, specifies target corridor lane (Lane 2 Center), and queries optimal clearance path.
- **Driver / In-Vehicle UI**: Receives lane yielding recommendations (`MOVE_LEFT`, `MOVE_RIGHT`, `REDUCE_SPEED`), views the live traffic map, and inspects the Local Digital Twin.
- **Traffic Authority**: Updates road network geometry, lane capacities, and static congestion thresholds.

---

## 3. Sequence Diagram
*(Referenced from Slide 12: Sequence Diagram)*

### Diagram
```mermaid
sequenceDiagram
    autonumber
    actor Driver as Driver / EV Operator
    participant Vehicle as Ego Vehicle
    participant Sensors as On-board Sensors
    participant V2X as V2X Crypto & Comm
    participant Nearby as Nearby Vehicles
    participant LDT as Local Digital Twin
    participant AI as AI Predictors (LSTM/XGB)
    participant Swarm as Swarm Engine (DPSO)
    participant Router as A* Navigation Router
    participant Dashboard as React Dashboard

    Driver->>Vehicle: Initiate dispatch / Drive
    Vehicle->>Sensors: Request telemetry (GPS, speed, lane, heading)
    Sensors-->>Vehicle: Return raw telemetry
    Vehicle->>V2X: Generate beacon + Sign with ECDSA (P-256)
    V2X->>Nearby: Broadcast signed beacon / Emergency announcement
    Nearby-->>V2X: Receive neighboring vehicle beacons
    V2X->>V2X: Verify ECDSA signatures, check freshness & sequence replay

    V2X->>LDT: Integrate authenticated telemetry into Local Twin
    LDT->>LDT: Discover neighbors (<450m) & calculate relative headways
    LDT->>AI: Query future states (History -> LSTM; Behaviour -> XGBoost)
    AI-->>LDT: Return 5-step predicted trajectory + Yielding probability

    LDT->>Swarm: Provide ego & neighbor twins, trust weights & compliance
    Swarm->>Swarm: Run DPSO particles (optimize lateral movements & headway)
    Swarm->>Swarm: Check safety constraints & resolve movement conflicts
    Swarm-->>Router: Pass clearance readiness of primary corridor lanes

    Router->>Router: Execute A* search with congestion & blockage penalties
    alt Vehicle yields as expected
        Router-->>Dashboard: Return optimal Market St Corridor (INT_1 -> INT_5)
    else Driver fails to yield (Obstruction detected)
        Swarm->>Router: Report non-yielding blockage on segment
        Router->>Router: Dynamically re-weight edge & replan via Mission Bypass
        Router-->>Dashboard: Return updated dynamic replanned route
    end

    Swarm-->>Vehicle: Dispatched recommended actions (MOVE_LEFT, REDUCE_SPEED)
    Vehicle-->>Driver: Display lane yield prompt & headway warning
    Dashboard-->>Driver: Render live corridor map, twin telemetry & alerts
```

### Execution Trace
1. **Sensory Polling**: Onboard sensors register speed, lane, heading, and distance to emergency vehicles.
2. **Cryptographic Transmission**: Packets are authenticated with ECDSA signatures and SHA-256 digests.
3. **Local World Integration**: Local Digital Twins assimilate authenticated neighbors within radio range ($<450$m).
4. **Machine Learning Inference**: Concurrently queries PyTorch LSTM for future positions and XGBoost for yielding compliance.
5. **Swarm Convergence**: DPSO evaluates candidate action vectors across all participating agents to minimize delay and maximize safety headway.
6. **Dynamic Replanning**: If an obstruction is detected (e.g., V004 refuses to yield), the system triggers dynamic A\* replanning in real time.

---

## 4. Activity Diagram
*(Synthesizing Operational Control Flow & Replanning Branching)*

### Diagram
```mermaid
flowchart TD
    START([Start Emergency Corridor Operation]) --> EV_DISPATCH["Emergency Vehicle (EV01) Dispatches Active Call"]
    EV_DISPATCH --> BCAST_SIG["Sign & Broadcast ECDSA Emergency Announcement"]
    BCAST_SIG --> V2X_CHECK{"Verify Signature & Freshness (<15s)?"}

    V2X_CHECK -- No / Tampered / Replay --> DROP_MSG["Reject Corrupted Beacon & Log Security Audit"] --> WAIT_NEXT["Wait for Next Beacon Cycle"]
    V2X_CHECK -- Yes / Valid --> PARALLEL_EVAL["Parallel Perception & Trust Evaluation"]

    subgraph DUAL_PIPELINE["Multi-Agent Intelligence Processing"]
        PARALLEL_EVAL --> TRUST_EVAL["Compute Behavioural Trust: T = w1*P + w2*C + w3*F + w4*S"]
        PARALLEL_EVAL --> ANOM_DETECT["Run Isolation Forest on Speed, Acceleration & Displacement"]
        PARALLEL_EVAL --> TRAJ_PRED["PyTorch LSTM: Forecast 5-Step Trajectories"]
        PARALLEL_EVAL --> COMP_PRED["XGBoost: Predict Driver Yielding Propensity"]

        TRUST_EVAL --> MERGE_LDT["Update Independent Local Digital Twins"]
        ANOM_DETECT --> MERGE_LDT
        TRAJ_PRED --> MERGE_LDT
        COMP_PRED --> MERGE_LDT
    end

    MERGE_LDT --> TRUST_FILTER{"Is Vehicle Trust >= 0.45 (Not Suspicious)?"}
    TRUST_FILTER -- No --> QUARANTINE["Quarantine Node: Exclude from Corridor Swarm Calculations"]
    TRUST_FILTER -- Yes --> SWARM_INIT["Include in DPSO Swarm Optimization Agents"]

    QUARANTINE --> SWARM_INIT
    SWARM_INIT --> RUN_DPSO["Execute DPSO: Minimize Multi-Objective Delay & Safety Fitness"]
    RUN_DPSO --> RUN_ASTAR["Run A* Graph Router with Current Edge Congestion Costs"]

    RUN_ASTAR --> ISSUE_DIRECTIVES["Dispatch Recommended Movement Directives (e.g., MOVE_LEFT, REDUCE_SPEED)"]
    ISSUE_DIRECTIVES --> MONITOR_CORRIDOR{"Do All Corridor Vehicles Yield Successfully?"}

    MONITOR_CORRIDOR -- Yes --> CORRIDOR_CLEAR["Corridor Formed: Ambulance Transits at Free-Flow Speed"]
    MONITOR_CORRIDOR -- No (Driver Blocks Lane) --> DETECT_BLOCK["Detect Corridor Bottleneck / Failed Yielding"]

    subgraph REPLAN_CYCLE["Dynamic Replanning Sub-Loop"]
        DETECT_BLOCK --> PENALIZE_EDGE["Penalize Blocked Road Segment (Weight += 9999)"]
        PENALIZE_EDGE --> RE_DPSO["Trigger DPSO Re-Coordination for Bypass Path"]
        RE_DPSO --> RE_ASTAR["Recompute Route via A* (Divert via Mission St Bypass)"]
        RE_ASTAR --> UPDATE_UI["Update Dashboard with Dynamic Replan Alert & New Route"]
    end

    UPDATE_UI --> CORRIDOR_CLEAR
    CORRIDOR_CLEAR --> END_NODE([Ambulance Arrives at Destination])
```

---

## 5. Generated Documentation Artifacts

1. **Word Document (`.docx`)**:
   - Location: [`Emergency_Vehicle_Corridor_Coordination_Design_Document.docx`](file:///c:/Users/rishi/Downloads/Krishna%20Teja/Emergency_Vehicle_Corridor_Coordination_Design_Document.docx)
   - Size: ~2.85 MB
   - Features: Formatted typography, author metadata, executive summary, callout cards, step-by-step numbered breakdowns, and **embedded high-resolution images** for all diagrams (System Architecture, Use Case, Sequence, Activity, and Class Diagrams).
2. **Markdown Specification**:
   - Location: [`ARCHITECTURE_AND_DESIGN_DOCUMENT.md`](file:///c:/Users/rishi/Downloads/Krishna%20Teja/ARCHITECTURE_AND_DESIGN_DOCUMENT.md)
   - Features: Full Mermaid diagram code blocks ready for GitHub rendering.

