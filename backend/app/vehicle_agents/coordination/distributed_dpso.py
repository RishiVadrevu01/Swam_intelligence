import random
import numpy as np
from typing import Dict, List, Any, Tuple, Optional


ACTION_NAMES = [
    "MAINTAIN_POSITION",  # 0
    "MOVE_LEFT",          # 1
    "MOVE_RIGHT",         # 2
    "REDUCE_SPEED",       # 3
    "MAINTAIN_GAP"        # 4
]


class DistributedParticle:
    """
    Candidate solution maintained independently by an agent.
    Each particle encodes the agent's action and its current perception of neighbors.
    """

    def __init__(self, action_idx: int = 0):
        self.action_idx: int = action_idx
        self.velocity: float = 0.0
        self.p_best_action: int = action_idx
        self.p_best_fitness: float = float('inf')
        self.current_fitness: float = float('inf')


class DistributedDPSOCoordinator:
    """
    Implements Formula 1 from the research paper:
    J = alpha * T_e + beta * D_n + gamma * R_s + delta * C_m + epsilon * N_nc
    
    Where:
    - T_e: Emergency vehicle travel time
    - D_n: Aggregate delay experienced by normal vehicles
    - R_s: Safety-risk penalty (headway & collision risk)
    - C_m: Communication cost (messages/bytes in local neighborhood)
    - N_nc: Number or weighted severity of non-compliant responses
    
    Safety constraints (collision avoidance and lane limits) are HARD constraints.
    Each agent updates its particle using its personal best (pBest) and the neighborhood
    best (nBest) received from its local V2V communication peers.
    """

    def __init__(
        self,
        vehicle_id: str,
        alpha: float = 3.5,  # Emergency travel time weight
        beta: float = 2.0,   # Normal traffic delay weight
        gamma: float = 4.0,  # Safety-risk penalty weight
        delta: float = 1.0,  # Communication cost weight
        epsilon: float = 2.5,# Non-compliance penalty weight
        w: float = 0.65,     # Inertia
        c1: float = 1.4,     # Cognitive (pBest)
        c2: float = 1.6      # Social (nBest)
    ):
        self.vehicle_id = vehicle_id
        self.weights = {
            "alpha": alpha,
            "beta": beta,
            "gamma": gamma,
            "delta": delta,
            "epsilon": epsilon
        }
        self.w = w
        self.c1 = c1
        self.c2 = c2

        self.particle = DistributedParticle(action_idx=0)
        self.convergence_history: List[Dict[str, float]] = []
        self.last_objective_breakdown: Dict[str, float] = {}

    def evaluate_local_objective(
        self,
        candidate_action_idx: int,
        ego_state: Dict[str, Any],
        ev_state: Optional[Dict[str, Any]],
        neighbor_states: List[Dict[str, Any]],
        driver_compliance_prob: float,
        trust_scores: Dict[str, float],
        local_messages_count: int = 5
    ) -> Tuple[float, Dict[str, float], bool]:
        """
        Evaluates J = alpha*T_e + beta*D_n + gamma*R_s + delta*C_m + epsilon*N_nc
        Enforces HARD constraints: returns is_feasible = False if collision or invalid lane change.
        """
        action_name = ACTION_NAMES[candidate_action_idx]
        cur_lane = int(ego_state.get("current_lane", 2))
        cur_speed = float(ego_state.get("speed", 40.0))
        target_ev_lane = int(ev_state.get("target_lane", 2)) if ev_state else 2

        # 1. HARD CONSTRAINT: Lane geometry boundary check
        resulting_lane = cur_lane
        if action_name == "MOVE_LEFT":
            if cur_lane <= 1:
                return float('inf'), {}, False  # Illegal left turn off road
            resulting_lane = cur_lane - 1
        elif action_name == "MOVE_RIGHT":
            if cur_lane >= 3:
                return float('inf'), {}, False  # Illegal right turn off road
            resulting_lane = cur_lane + 1

        # 2. HARD CONSTRAINT: Collision avoidance / Headway with neighbors in resulting lane
        r_s_safety_risk = 0.0
        for n in neighbor_states:
            n_lane = int(n.get("lane", n.get("current_lane", 1)))
            n_dist = float(n.get("distance_meters", 100.0))
            n_trust = trust_scores.get(n.get("vehicle_id", ""), 0.85)

            # If neighbor is in our target lane and within hazardous proximity (< 14m)
            if n_lane == resulting_lane and n_dist < 14.0:
                # Violates hard safety constraint
                return float('inf'), {}, False

            if n_lane == resulting_lane and n_dist < 22.0:
                r_s_safety_risk += (22.0 - n_dist) * 0.15 * (1.2 - 0.2 * n_trust)

        # 3. T_e: Emergency Vehicle Delay Component
        t_e_delay = 0.0
        if ev_state and ev_state.get("active", True):
            ev_dist = float(ego_state.get("distance_to_ev", 150.0))
            if resulting_lane == target_ev_lane and ev_dist < 250.0:
                # Vehicle blocks emergency vehicle passage
                t_e_delay = (250.0 - ev_dist) / 50.0  # seconds of delay imposed
            else:
                t_e_delay = 0.0  # Successfully clears corridor

        # 4. D_n: Normal Traffic Delay Component
        d_n_delay = 0.0
        if action_name == "REDUCE_SPEED":
            d_n_delay = 1.8  # Slight speed reduction penalty
        elif action_name in ["MOVE_LEFT", "MOVE_RIGHT"]:
            d_n_delay = 0.9  # Minor lane transition delay
        else:
            d_n_delay = 0.2

        # 5. C_m: Communication Cost Component
        c_m_cost = min(2.0, local_messages_count * 0.1)

        # 6. N_nc: Non-Compliance Severity
        # If low compliance driver is commanded to do complex maneuver, likelihood of refusal is high
        n_nc_severity = 0.0
        if action_name in ["MOVE_LEFT", "MOVE_RIGHT"]:
            n_nc_severity = max(0.0, 1.0 - driver_compliance_prob) * 2.0
        elif action_name == "REDUCE_SPEED":
            n_nc_severity = max(0.0, 1.0 - driver_compliance_prob) * 1.0

        # Weighted sum of components
        alpha = self.weights["alpha"]
        beta = self.weights["beta"]
        gamma = self.weights["gamma"]
        delta = self.weights["delta"]
        epsilon = self.weights["epsilon"]

        total_fitness = (
            (alpha * t_e_delay) +
            (beta * d_n_delay) +
            (gamma * r_s_safety_risk) +
            (delta * c_m_cost) +
            (epsilon * n_nc_severity)
        )

        breakdown = {
            "T_e_emergency_delay": round(t_e_delay, 3),
            "D_n_traffic_delay": round(d_n_delay, 3),
            "R_s_safety_risk": round(r_s_safety_risk, 3),
            "C_m_comm_cost": round(c_m_cost, 3),
            "N_nc_non_compliance": round(n_nc_severity, 3),
            "total_J": round(total_fitness, 4)
        }

        return total_fitness, breakdown, True

    def step_distributed_dpso(
        self,
        ego_state: Dict[str, Any],
        ev_state: Optional[Dict[str, Any]],
        neighbor_states: List[Dict[str, Any]],
        neighbor_candidates: List[Dict[str, Any]],
        driver_compliance_prob: float,
        trust_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Executes one iteration of distributed PSO update using local neighborhood information.
        """
        num_actions = len(ACTION_NAMES)

        # 1. Evaluate current candidate
        fit, breakdown, feasible = self.evaluate_local_objective(
            self.particle.action_idx,
            ego_state,
            ev_state,
            neighbor_states,
            driver_compliance_prob,
            trust_scores
        )

        if feasible and fit < self.particle.p_best_fitness:
            self.particle.p_best_fitness = fit
            self.particle.p_best_action = self.particle.action_idx
            self.last_objective_breakdown = breakdown

        self.particle.current_fitness = fit

        # 2. Determine neighborhood best (nBest) from local peers
        n_best_action = self.particle.p_best_action
        n_best_fitness = self.particle.p_best_fitness

        for peer in neighbor_candidates:
            peer_fit = peer.get("personal_best_fitness", float('inf'))
            peer_act = peer.get("candidate_action_idx", 0)
            if peer_fit < n_best_fitness:
                n_best_fitness = peer_fit
                n_best_action = peer_act

        # 3. Update velocity & position
        r1 = random.random()
        r2 = random.random()

        self.particle.velocity = (
            self.w * self.particle.velocity +
            self.c1 * r1 * (self.particle.p_best_action - self.particle.action_idx) +
            self.c2 * r2 * (n_best_action - self.particle.action_idx)
        )

        # Velocity clamping
        self.particle.velocity = max(-2.0, min(2.0, self.particle.velocity))

        # Position update (probabilistic discrete transition)
        new_pos = self.particle.action_idx + self.particle.velocity
        candidate_idx = int(np.clip(round(new_pos), 0, num_actions - 1))

        # Check feasibility of candidate
        cand_fit, cand_break, cand_feas = self.evaluate_local_objective(
            candidate_idx,
            ego_state,
            ev_state,
            neighbor_states,
            driver_compliance_prob,
            trust_scores
        )

        if cand_feas:
            self.particle.action_idx = candidate_idx
        else:
            # Fallback to personal best action if candidate violates hard constraints
            self.particle.action_idx = self.particle.p_best_action

        # Record convergence
        self.convergence_history.append({
            "iteration": len(self.convergence_history) + 1,
            "best_fitness": round(self.particle.p_best_fitness, 4),
            "current_action": ACTION_NAMES[self.particle.action_idx]
        })
        if len(self.convergence_history) > 30:
            self.convergence_history.pop(0)

        best_act_name = ACTION_NAMES[self.particle.p_best_action]
        cur_lane = int(ego_state.get("current_lane", 2))
        target_lane = cur_lane
        if best_act_name == "MOVE_LEFT":
            target_lane = max(1, cur_lane - 1)
        elif best_act_name == "MOVE_RIGHT":
            target_lane = min(3, cur_lane + 1)

        return {
            "vehicle_id": self.vehicle_id,
            "recommended_action": best_act_name,
            "current_lane": cur_lane,
            "recommended_lane": target_lane,
            "fitness": round(self.particle.p_best_fitness, 4),
            "objective_breakdown": self.last_objective_breakdown,
            "feasible": True
        }

    def get_public_candidate(self) -> Dict[str, Any]:
        return {
            "vehicle_id": self.vehicle_id,
            "action_idx": self.particle.action_idx,
            "action_name": ACTION_NAMES[self.particle.action_idx],
            "p_best_action": ACTION_NAMES[self.particle.p_best_action],
            "p_best_fitness": round(self.particle.p_best_fitness, 4) if self.particle.p_best_fitness != float('inf') else None,
            "velocity": round(self.particle.velocity, 3)
        }

