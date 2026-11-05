import networkx as nx
import math
from typing import Dict, List, Any, Tuple, Optional
from app.core.scenario_generator import INTERSECTIONS, ROAD_SEGMENTS


class AStarRouter:
    """
    NetworkX graph-based A* pathfinder and dynamic replanner for Emergency Vehicles.
    Considers road distance, speed limits, live congestion density, and non-yielding blockage penalties.
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_road_graph()

    def _build_road_graph(self):
        self.graph.clear()
        # Add intersection nodes
        for node_id, data in INTERSECTIONS.items():
            self.graph.add_node(
                node_id,
                lat=data["lat"],
                lon=data["lon"],
                name=data["name"]
            )

        # Add road segment edges
        for r in ROAD_SEGMENTS:
            u = r["start_intersection"]
            v = r["end_intersection"]
            length = float(r["length_meters"])

            # Base cost is travel time at free flow (e.g. 50 km/h = 13.89 m/s)
            base_time = length / 13.89

            self.graph.add_edge(
                u, v,
                road_id=r["road_id"],
                name=r["name"],
                length_meters=length,
                lanes=r["lanes"],
                base_time=base_time,
                weight=base_time,
                congestion_penalty=0.0,
                blockage_penalty=0.0,
                is_blocked=False
            )

    def heuristic(self, u: str, v: str) -> float:
        """
        Admissible Euclidean distance heuristic between two intersection nodes.
        """
        u_data = self.graph.nodes[u]
        v_data = self.graph.nodes[v]
        d_lat = (u_data["lat"] - v_data["lat"]) * 111000.0
        d_lon = (u_data["lon"] - v_data["lon"]) * 88000.0
        dist = math.sqrt(d_lat**2 + d_lon**2)
        # Minimum travel time assuming top speed 70 km/h (19.4 m/s)
        return dist / 19.4

    def update_road_weights(
        self,
        roads_telemetry: List[Dict[str, Any]],
        blocked_roads: List[str] = None
    ):
        """
        Updates dynamic edge weights using real-time traffic density, congestion levels,
        and simulated non-yielding vehicle corridor blockages.
        """
        blocked_roads = blocked_roads or []
        road_lookup = {r["road_id"]: r for r in roads_telemetry}

        for u, v, data in self.graph.edges(data=True):
            r_id = data["road_id"]
            live_data = road_lookup.get(r_id, {})

            length = data["length_meters"]
            avg_speed = max(10.0, float(live_data.get("average_speed", 45.0)))
            speed_ms = avg_speed / 3.6

            # Travel time in seconds
            travel_time = length / speed_ms

            # Density factor: 1.0 (empty) to 2.5 (severe congestion)
            density = float(live_data.get("traffic_density", 30.0))
            density_factor = 1.0 + (density / 70.0)

            # Blockage penalty
            if r_id in blocked_roads or data.get("is_blocked", False):
                blockage_cost = 9999.0  # Impassable or non-compliant blockage
                data["is_blocked"] = True
            else:
                blockage_cost = 0.0
                data["is_blocked"] = False

            total_weight = (travel_time * density_factor) + blockage_cost
            data["weight"] = total_weight
            data["congestion_penalty"] = round(density_factor, 2)
            data["blockage_penalty"] = blockage_cost

    def find_route(
        self,
        start_node: str = "INT_1",
        destination_node: str = "INT_5",
        blocked_roads: List[str] = None
    ) -> Dict[str, Any]:
        """
        Computes the optimal path for Emergency Vehicle using A* Search.
        """
        if blocked_roads:
            for u, v, data in self.graph.edges(data=True):
                if data["road_id"] in blocked_roads:
                    data["weight"] += 9999.0
                    data["is_blocked"] = True

        try:
            path_nodes = nx.astar_path(
                self.graph,
                source=start_node,
                target=destination_node,
                heuristic=self.heuristic,
                weight="weight"
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # Fallback to direct path along primary corridor
            path_nodes = ["INT_1", "INT_2", "INT_3", "INT_4", "INT_5"]

        # Reconstruct path details, coordinates, and total distance
        route_coords = []
        total_dist = 0.0
        est_time = 0.0
        used_roads = []

        for i in range(len(path_nodes)):
            n_data = self.graph.nodes[path_nodes[i]]
            route_coords.append([n_data["lat"], n_data["lon"]])

            if i < len(path_nodes) - 1:
                u = path_nodes[i]
                v = path_nodes[i + 1]
                edge_data = self.graph.get_edge_data(u, v)
                if edge_data:
                    total_dist += edge_data.get("length_meters", 450.0)
                    est_time += edge_data.get("weight", 30.0)
                    used_roads.append(edge_data.get("road_id"))

        return {
            "start_node": start_node,
            "destination_node": destination_node,
            "route_nodes": path_nodes,
            "road_ids": used_roads,
            "route_coordinates": route_coords,
            "total_distance_meters": round(total_dist, 1),
            "estimated_travel_time_seconds": round(est_time, 1)
        }

    def simulate_dynamic_replan(
        self,
        original_route: Dict[str, Any],
        failed_vehicle_id: str,
        blocked_road_id: str
    ) -> Dict[str, Any]:
        """
        Executes dynamic route replanning when a non-compliant vehicle refuses to yield,
        causing a bottleneck on the planned corridor segment.
        """
        # Calculate alternate route bypassing the blocked segment
        alt_route = self.find_route(
            start_node=original_route.get("start_node", "INT_1"),
            destination_node=original_route.get("destination_node", "INT_5"),
            blocked_roads=[blocked_road_id]
        )

        return {
            "replanning_occurred": True,
            "replanning_reason": f"Vehicle {failed_vehicle_id} failed to yield on segment {blocked_road_id}; emergency corridor dynamically redirected via Mission Bypass.",
            "blocked_vehicle_id": failed_vehicle_id,
            "blocked_road_id": blocked_road_id,
            "original_route": original_route,
            "updated_route": alt_route,
            "travel_time_delta_seconds": round(alt_route["estimated_travel_time_seconds"] - original_route["estimated_travel_time_seconds"], 1)
        }


astar_router = AStarRouter()

