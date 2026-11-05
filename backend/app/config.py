import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "app" / "data"
MODELS_DIR = BASE_DIR / "app" / "ml" / "saved_models"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Trust calculation weights: T(i) = w1*P + w2*C + w3*F + w4*S
TRUST_WEIGHTS = {
    "w1_position": 0.35,      # Position plausibility
    "w2_movement": 0.25,      # Movement consistency
    "w3_freshness": 0.20,     # Message freshness
    "w4_sensor": 0.20         # Sensor consistency
}

# Trust thresholds
TRUST_THRESHOLDS = {
    "high": 0.75,
    "medium": 0.45,
    "low": 0.0
}

# DPSO parameters
DPSO_CONFIG = {
    "num_particles": 25,
    "max_iterations": 30,
    "w": 0.65,       # Inertia weight
    "c1": 1.4,       # Cognitive coefficient (local best)
    "c2": 1.6,       # Social coefficient (global/neighborhood best)
    # Objective weights in Fitness Function:
    # Fitness = alpha*EmergencyDelay + beta*SafetyPenalty + gamma*TrafficDelay + delta*ConflictPenalty + epsilon*CompliancePenalty
    "alpha": 3.5,
    "beta": 4.0,
    "gamma": 1.5,
    "delta": 3.0,
    "epsilon": 2.5
}

# V2X Security parameters
SECURITY_CONFIG = {
    "message_validity_window_seconds": 15.0,
    "max_sequence_number_gap": 100
}

