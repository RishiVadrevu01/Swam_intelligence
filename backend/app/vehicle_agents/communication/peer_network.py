import math
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable


def calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Haversine distance in meters
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class PeerToPeerNetwork:
    """
    Decentralized Peer-to-Peer V2V Communication Medium.
    Enforces communication neighborhood N_i(t) based on spatial proximity (< 450m).
    Measures communication overhead (messages sent, bytes transferred) for evaluation.
    """

    def __init__(self, communication_range_meters: float = 450.0):
        self.communication_range = communication_range_meters
        # vehicle_id -> agent_instance
        self.registered_agents: Dict[str, Any] = {}
        # Metrics for Formula 1 & Table 2
        self.total_messages_sent: int = 0
        self.total_bytes_transferred: int = 0
        self.messages_dropped: int = 0
        # Simulated fault injection (e.g. offline agent)
        self.offline_agents: set = set()
        # Message log for auditing
        self.transmission_log: List[Dict[str, Any]] = []

    def register_agent(self, agent: Any):
        self.registered_agents[agent.vehicle_id] = agent

    def unregister_agent(self, vehicle_id: str):
        if vehicle_id in self.registered_agents:
            del self.registered_agents[vehicle_id]

    def set_agent_offline(self, vehicle_id: str, offline: bool = True):
        if offline:
            self.offline_agents.add(vehicle_id)
        else:
            self.offline_agents.discard(vehicle_id)

    def broadcast(self, sender_id: str, sender_lat: float, sender_lon: float, message: Dict[str, Any]):
        """
        Broadcasts message to all agents within the communication neighborhood N_i(t).
        """
        if sender_id in self.offline_agents:
            return

        self.total_messages_sent += 1
        msg_bytes = len(str(message).encode('utf-8'))
        self.total_bytes_transferred += msg_bytes

        recipients = []
        for peer_id, peer in self.registered_agents.items():
            if peer_id == sender_id:
                continue
            if peer_id in self.offline_agents:
                self.messages_dropped += 1
                continue

            peer_lat = peer.state.latitude
            peer_lon = peer.state.longitude
            dist = calculate_distance_meters(sender_lat, sender_lon, peer_lat, peer_lon)

            # Enforce spatial neighborhood constraint N_i(t)
            if dist <= self.communication_range:
                recipients.append(peer_id)
                peer.receive_v2x_message(message, dist)

        log_entry = {
            "timestamp": time.time(),
            "sender_id": sender_id,
            "message_type": message.get("message_type"),
            "seq": message.get("sequence_number"),
            "recipient_count": len(recipients),
            "bytes": msg_bytes
        }
        self.transmission_log.append(log_entry)
        if len(self.transmission_log) > 200:
            self.transmission_log.pop(0)

    def get_communication_stats(self) -> Dict[str, Any]:
        return {
            "total_messages_sent": self.total_messages_sent,
            "total_bytes_transferred": self.total_bytes_transferred,
            "total_kb_transferred": round(self.total_bytes_transferred / 1024.0, 2),
            "messages_dropped": self.messages_dropped,
            "registered_nodes_count": len(self.registered_agents),
            "communication_range_meters": self.communication_range
        }

    def get_total_bytes_transmitted(self) -> int:
        return self.total_bytes_transferred


# Singleton default network instance for the in-memory agent cluster
peer_network = PeerToPeerNetwork()

