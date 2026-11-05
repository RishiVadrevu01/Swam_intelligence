import time
import random
import numpy as np
from typing import Dict, List, Any, Tuple
from app.config import DPSO_CONFIG


# Discrete Coordination Action definitions:
# 0: MAINTAIN_POSITION
# 1: MOVE_LEFT (yield to left lane)
# 2: MOVE_RIGHT (yield to right lane)
# 3: REDUCE_SPEED (slow down to create longitudinal gap)
# 4: MAINTAIN_GAP (hold distance)
ACTION_NAMES = [
    "MAINTAIN_POSITION",
    "MOVE_LEFT",
    "MOVE_RIGHT",
    "REDUCE_SPEED",
    "MAINTAIN_GAP"
]


class DPSOCoordinationEngine:
    """
    Distributed Particle Swarm Optimization (DPSO) engine for cooperative multi-vehicle corridor creation.
    Minimizes multi-objective fitness:
    Fitness = alpha*EmergencyDelay + beta*SafetyPenalty + gamma*TrafficDelay + delta*ConflictPenalty + epsilon*CompliancePenalty
    """
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DPSO_CONFIG

    def coordinate_vehicles(
        self,
        participating_vehicles: List[Dict[str, Any]],
        emergency_vehicle: Dict[str, Any],
        compliance_map: Dict[str, float] = None,
        trust_map: Dict[str, float] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        compliance_map = compliance_map or {}
        trust_map = trust_map or {}

        num_agents = len(participating_vehicles)
        if num_agents == 0:
            return {
                "participating_agents": [],
                "total_iterations": 0,
                "initial_fitness": 0.0,
                "best_fitness": 0.0,
                "convergence_history": [],
                "recommended_actions": [],
                "conflicts_detected": 0,
                "objective_breakdown": {},
                "execution_time_ms": 0.0
            }

        # DPSO hyperparameters
        num_particles = self.config.get("num_particles", 25)
        max_iters = self.config.get("max_iterations", 30)
        w = self.config.get("w", 0.65)
        c1 = self.config.get("c1", 1.4)
        c2 = self.config.get("c2", 1.6)

        alpha = self.config.get("alpha", 3.5)
        beta = self.config.get("beta", 4.0)
        gamma = self.config.get("gamma", 1.5)
        delta = self.config.get("delta", 3.0)
        epsilon = self.config.get("epsilon", 2.5)

        # Action space: 0 to 4 (5 discrete action states)
        num_actions = len(ACTION_NAMES)

        # Target lane for emergency vehicle (Lane 2 - center lane)
        ev_target_lane = emergency_vehicle.get("target_lane", 2)

        # 1. Initialize Particles (positions & velocities in continuous space, discretised via round/modulo)
        # Position shape: (num_particles, num_agents) with values in [0, num_actions - 1]
        np.random.seed(42)
        positions = np.random.uniform(0.0, num_actions - 1e-4, size=(num_particles, num_agents))
        velocities = np.random.uniform(-1.5, 1.5, size=(num_particles, num_agents))

        # Personal bests
        p_best_pos = np.copy(positions)
        p_best_fit = np.full(num_particles, float('inf'))

        # Global best
        g_best_pos = None
        g_best_fit = float('inf')
        g_best_breakdown = {}

        convergence_history = []
        initial_fitness_val = None

        # 2. DPSO Iteration Loop
        for it in range(max_iters):
            iter_fitness_vals = []

            for p_idx in range(num_particles):
                # Discretize continuous particle position to candidate actions
                actions_discrete = np.clip(np.round(positions[p_idx]), 0, num_actions - 1).astype(int)

                fitness, breakdown = self._evaluate_fitness(
                    actions_discrete=actions_discrete,
                    vehicles=participating_vehicles,
                    ev_target_lane=ev_target_lane,
                    compliance_map=compliance_map,
                    trust_map=trust_map,
                    alpha=alpha, beta=beta, gamma=gamma, delta=delta, epsilon=epsilon
                )

                iter_fitness_vals.append(fitness)

                # Update personal best
                if fitness < p_best_fit[p_idx]:
                    p_best_fit[p_idx] = fitness
                    p_best_pos[p_idx] = np.copy(positions[p_idx])

                # Update global best
                if fitness < g_best_fit:
                    g_best_fit = fitness
                    g_best_pos = np.copy(positions[p_idx])
                    g_best_breakdown = breakdown

            avg_fit = float(np.mean(iter_fitness_vals))
            if initial_fitness_val is None:
                initial_fitness_val = g_best_fit

            convergence_history.append({
                "iteration": it + 1,
                "best_fitness": round(float(g_best_fit), 4),
                "average_fitness": round(avg_fit, 4)
            })

            # Velocity and position updates
            r1 = np.random.uniform(0.0, 1.0, size=(num_particles, num_agents))
            r2 = np.random.uniform(0.0, 1.0, size=(num_particles, num_agents))

            velocities = (
                w * velocities +
                c1 * r1 * (p_best_pos - positions) +
                c2 * r2 * (g_best_pos - positions)
            )
            # Velocity clamping
            velocities = np.clip(velocities, -2.0, 2.0)
            positions = np.clip(positions + velocities, 0.0, num_actions - 1e-4)

        # 3. Construct Final Recommendations based on best particle
        best_actions = np.clip(np.round(g_best_pos), 0, num_actions - 1).astype(int)
        recommended_actions = []
        conflicts = 0

        for i, v in enumerate(participating_vehicles):
            vid = v["vehicle_id"]
            cur_lane = int(v.get("current_lane", 2))
            speed = float(v.get("speed", 40.0))
            act_idx = int(best_actions[i])
            act_name = ACTION_NAMES[act_idx]

            rec_lane = cur_lane
            target_speed = speed
            reason = ""

            # Check if this vehicle is currently blocking the EV's target lane
            in_ev_corridor = (cur_lane == ev_target_lane)

            if act_name == "MOVE_LEFT":
                rec_lane = max(1, cur_lane - 1)
                target_speed = speed * 0.95
                reason = "Vacate center corridor to left lane"
            elif act_name == "MOVE_RIGHT":
                rec_lane = min(3, cur_lane + 1)
                target_speed = speed * 0.95
                reason = "Vacate center corridor to right lane"
            elif act_name == "REDUCE_SPEED":
                rec_lane = cur_lane
                target_speed = max(15.0, speed * 0.70)
                reason = "Decelerate to create safe longitudinal corridor gap"
            elif act_name == "MAINTAIN_GAP":
                rec_lane = cur_lane
                target_speed = speed * 0.90
                reason = "Hold current lateral position with increased safety headway"
            else:
                rec_lane = cur_lane
                target_speed = speed
                reason = "Maintain lane; outside primary emergency trajectory"

            # Check conflict with neighbours moving into identical lane at close distance
            conflict = False
            for j, other_v in enumerate(participating_vehicles):
                if i != j:
                    other_rec_lane = cur_lane
                    other_act = ACTION_NAMES[best_actions[j]]
                    if other_act == "MOVE_LEFT":
                        other_rec_lane = max(1, other_v.get("current_lane", 2) - 1)
                    elif other_act == "MOVE_RIGHT":
                        other_rec_lane = min(3, other_v.get("current_lane", 2) + 1)

                    if rec_lane == other_rec_lane:
                        # Distance check
                        d_lat = abs(v.get("latitude", 0) - other_v.get("latitude", 0))
                        d_lon = abs(v.get("longitude", 0) - other_v.get("longitude", 0))
                        approx_dist = ((d_lat * 111000)**2 + (d_lon * 88000)**2)**0.5
                        if approx_dist < 18.0:
                            conflict = True
                            conflicts += 1
                            break

            compliance_likelihood = compliance_map.get(vid, 0.85)

            recommended_actions.append({
                "vehicle_id": vid,
                "current_lane": cur_lane,
                "recommended_lane": rec_lane,
                "action_type": act_name,
                "target_speed": round(target_speed, 1),
                "safety_margin_meters": round(15.0 + (target_speed / 10.0), 1),
                "compliance_likelihood": round(compliance_likelihood, 2),
                "conflict_detected": conflict,
                "reason": reason
            })

        exec_time = (time.time() - start_time) * 1000.0

        return {
            "participating_agents": [v["vehicle_id"] for v in participating_vehicles],
            "total_iterations": max_iters,
            "initial_fitness": round(float(initial_fitness_val), 4),
            "best_fitness": round(float(g_best_fit), 4),
            "convergence_history": convergence_history,
            "recommended_actions": recommended_actions,
            "conflicts_detected": conflicts,
            "objective_breakdown": g_best_breakdown,
            "execution_time_ms": round(exec_time, 2)
        }

    def _evaluate_fitness(
        self,
        actions_discrete: np.ndarray,
        vehicles: List[Dict[str, Any]],
        ev_target_lane: int,
        compliance_map: Dict[str, float],
        trust_map: Dict[str, float],
        alpha: float, beta: float, gamma: float, delta: float, epsilon: float
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculates multi-objective fitness value:
        Fitness = alpha*EmergencyDelay + beta*SafetyPenalty + gamma*TrafficDelay + delta*ConflictPenalty + epsilon*CompliancePenalty
        """
        emergency_delay = 0.0
        safety_penalty = 0.0
        traffic_delay = 0.0
        conflict_penalty = 0.0
        compliance_penalty = 0.0

        n = len(vehicles)
        projected_lanes = []

        for i in range(n):
            v = vehicles[i]
            cur_lane = int(v.get("current_lane", 2))
            act = actions_discrete[i]
            vid = v.get("vehicle_id")

            # Determine resulting lane
            if act == 1:  # MOVE_LEFT
                new_lane = max(1, cur_lane - 1)
                traffic_delay += 0.35  # Minor lane change delay
            elif act == 2:  # MOVE_RIGHT
                new_lane = min(3, cur_lane + 1)
                traffic_delay += 0.35
            elif act == 3:  # REDUCE_SPEED
                new_lane = cur_lane
                traffic_delay += 0.60  # Speed reduction delay
            else:
                new_lane = cur_lane

            projected_lanes.append(new_lane)

            # 1. Emergency Delay: if vehicle remains in EV's intended corridor lane (e.g. Lane 2)
            if new_lane == ev_target_lane:
                emergency_delay += 2.8  # Major delay penalty to emergency vehicle

            # 2. Compliance Penalty: recommending complex lane changes to low-compliance drivers is penalized
            comp_prob = compliance_map.get(vid, 0.85)
            if act in [1, 2] and comp_prob < 0.40:
                # Driver likely to disobey lane change
                compliance_penalty += 1.8 * (1.0 - comp_prob)

            # 3. Trust-weighted attenuation
            t_score = trust_map.get(vid, 0.85)
            if t_score < 0.45:
                # Untrusted vehicle position may induce coordination noise
                safety_penalty += 0.90

        # 4. Conflict & Safety Headway Penalties between pairs of vehicles
        for i in range(n):
            for j in range(i + 1, n):
                if projected_lanes[i] == projected_lanes[j]:
                    # Estimate spatial distance
                    vi = vehicles[i]
                    vj = vehicles[j]
                    d_lat = abs(vi.get("latitude", 0) - vj.get("latitude", 0))
                    d_lon = abs(vi.get("longitude", 0) - vj.get("longitude", 0))
                    dist = ((d_lat * 111000)**2 + (d_lon * 88000)**2)**0.5

                    if dist < 12.0:
                        # Severe collision/headway safety risk
                        safety_penalty += 3.5
                    elif dist < 22.0:
                        conflict_penalty += 1.5

        # Normalize objectives
        f_em = emergency_delay / max(1.0, n * 2.0)
        f_safe = safety_penalty / max(1.0, n * 1.5)
        f_traf = traffic_delay / max(1.0, n * 0.8)
        f_conf = conflict_penalty / max(1.0, n * 1.0)
        f_comp = compliance_penalty / max(1.0, n * 1.0)

        total_fitness = (
            alpha * f_em +
            beta * f_safe +
            gamma * f_traf +
            delta * f_conf +
            epsilon * f_comp
        )

        breakdown = {
            "emergency_delay": round(f_em, 4),
            "safety_penalty": round(f_safe, 4),
            "traffic_delay": round(f_traf, 4),
            "conflict_penalty": round(f_conf, 4),
            "compliance_penalty": round(f_comp, 4),
            "total_fitness": round(total_fitness, 4)
        }

        return total_fitness, breakdown


dpso_engine = DPSOCoordinationEngine()

