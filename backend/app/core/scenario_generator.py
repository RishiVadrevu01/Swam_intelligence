import json
import random
import time
from typing import Dict, List, Any
from app.config import DATA_DIR
from app.core.cryptography import v2x_security


# 8 Urban Intersections forming a realistic arterial corridor grid
INTERSECTIONS = {
    "INT_1": {"lat": 37.7750, "lon": -122.4200, "name": "Market & 10th St"},
    "INT_2": {"lat": 37.7780, "lon": -122.4180, "name": "Market & 8th St"},
    "INT_3": {"lat": 37.7810, "lon": -122.4150, "name": "Market & 6th St"},
    "INT_4": {"lat": 37.7845, "lon": -122.4110, "name": "Market & 4th St"},
    "INT_5": {"lat": 37.7880, "lon": -122.4070, "name": "Market & 2nd St (Hospital Junction)"},
    "INT_6": {"lat": 37.7770, "lon": -122.4240, "name": "Mission & 10th St (Bypass)"},
    "INT_7": {"lat": 37.7805, "lon": -122.4200, "name": "Mission & 8th St (Bypass)"},
    "INT_8": {"lat": 37.7840, "lon": -122.4160, "name": "Mission & 5th St (Bypass)"}
}

ROAD_SEGMENTS = [
    {
        "road_id": "ROAD_01",
        "name": "Market St Segment 1",
        "start_intersection": "INT_1",
        "end_intersection": "INT_2",
        "length_meters": 450.0,
        "lanes": 3,
        "road_direction": "Northeast"
    },
    {
        "road_id": "ROAD_02",
        "name": "Market St Segment 2",
        "start_intersection": "INT_2",
        "end_intersection": "INT_3",
        "length_meters": 480.0,
        "lanes": 3,
        "road_direction": "Northeast"
    },
    {
        "road_id": "ROAD_03",
        "name": "Market St Segment 3 (Corridor Core)",
        "start_intersection": "INT_3",
        "end_intersection": "INT_4",
        "length_meters": 520.0,
        "lanes": 3,
        "road_direction": "Northeast"
    },
    {
        "road_id": "ROAD_04",
        "name": "Market St Segment 4 (Hospital Approach)",
        "start_intersection": "INT_4",
        "end_intersection": "INT_5",
        "length_meters": 550.0,
        "lanes": 3,
        "road_direction": "Northeast"
    },
    {
        "road_id": "ROAD_05",
        "name": "Mission St South Bypass",
        "start_intersection": "INT_1",
        "end_intersection": "INT_6",
        "length_meters": 420.0,
        "lanes": 2,
        "road_direction": "East"
    },
    {
        "road_id": "ROAD_06",
        "name": "Mission St Mid Bypass",
        "start_intersection": "INT_6",
        "end_intersection": "INT_7",
        "length_meters": 500.0,
        "lanes": 2,
        "road_direction": "Northeast"
    },
    {
        "road_id": "ROAD_07",
        "name": "Mission St North Bypass",
        "start_intersection": "INT_7",
        "end_intersection": "INT_8",
        "length_meters": 510.0,
        "lanes": 2,
        "road_direction": "Northeast"
    },
    {
        "road_id": "ROAD_08",
        "name": "5th St Cross Connector",
        "start_intersection": "INT_8",
        "end_intersection": "INT_4",
        "length_meters": 380.0,
        "lanes": 2,
        "road_direction": "North"
    },
    {
        "road_id": "ROAD_09",
        "name": "8th St Cross Connector",
        "start_intersection": "INT_7",
        "end_intersection": "INT_2",
        "length_meters": 360.0,
        "lanes": 2,
        "road_direction": "North"
    },
    {
        "road_id": "ROAD_10",
        "name": "Hospital Direct Emergency Ramp",
        "start_intersection": "INT_8",
        "end_intersection": "INT_5",
        "length_meters": 620.0,
        "lanes": 2,
        "road_direction": "Northeast"
    }
]


class ScenarioGenerator:
    """
    Generates synthetic datasets for urban road traffic, emergency vehicles,
    driver compliance behaviours, trust metrics, and V2X communication packets.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def generate_scenario(self, scenario_type: str = "Scenario A: Normal Emergency Corridor", vehicle_count: int = 25) -> Dict[str, Any]:
        random.seed(self.seed)

        # 1. Roads & Traffic Generation
        roads_data = []
        for r in ROAD_SEGMENTS:
            start_coord = INTERSECTIONS[r["start_intersection"]]
            end_coord = INTERSECTIONS[r["end_intersection"]]

            # Congestion based on scenario
            if "Scenario D" in scenario_type:
                density = random.uniform(55.0, 85.0)
                avg_speed = random.uniform(15.0, 28.0)
                congestion = "Severe" if density > 70 else "High"
                available_space = random.uniform(10.0, 25.0)
            else:
                density = random.uniform(20.0, 45.0)
                avg_speed = random.uniform(35.0, 52.0)
                congestion = "Moderate" if density > 35 else "Low"
                available_space = random.uniform(45.0, 80.0)

            road_entry = {
                "road_id": r["road_id"],
                "name": r["name"],
                "start_intersection": r["start_intersection"],
                "end_intersection": r["end_intersection"],
                "length_meters": r["length_meters"],
                "start_lat": start_coord["lat"],
                "start_lon": start_coord["lon"],
                "end_lat": end_coord["lat"],
                "end_lon": end_coord["lon"],
                "lanes": r["lanes"],
                "traffic_density": round(density, 1),
                "average_speed": round(avg_speed, 1),
                "road_capacity": 60,
                "congestion_level": congestion,
                "available_space": round(available_space, 1),
                "road_direction": r["road_direction"]
            }
            roads_data.append(road_entry)

        # 2. Emergency Vehicle Generation (EV01)
        # Positioned approaching Market St Segment 1 heading towards Hospital Junction (INT_5)
        ev_start = INTERSECTIONS["INT_1"]
        emergency_vehicle = {
            "emergency_vehicle_id": "EV01",
            "vehicle_type": "Ambulance",
            "latitude": round(ev_start["lat"] + 0.0003, 6),
            "longitude": round(ev_start["lon"] + 0.0002, 6),
            "speed": 62.5,
            "heading": 48.0,
            "destination": "INT_5 (Hospital Junction)",
            "priority_level": 1,
            "emergency_status": "ACTIVE_DISPATCH",
            "intended_route": ["ROAD_01", "ROAD_02", "ROAD_03", "ROAD_04"],
            "current_road_id": "ROAD_01",
            "target_lane": 2  # Center lane intended for emergency corridor
        }

        # 3. Normal Vehicles Generation
        normal_vehicles = []
        driver_behaviours = []
        trust_records = []
        v2x_messages = []

        now = time.time()
        vehicle_types = ["Sedan", "SUV", "Hatchback", "Coupe", "Pickup Truck", "Delivery Van"]

        # Select which vehicles will be anomalies or non-cooperative
        if "Scenario B" in scenario_type:
            # 35-40% non-compliant drivers
            low_compliance_indices = {2, 5, 8, 12, 17, 21}
        else:
            low_compliance_indices = {4, 18}

        if "Scenario C" in scenario_type:
            # Several suspicious anomalous vehicles
            suspicious_indices = {3, 7, 14, 22}
        else:
            suspicious_indices = {9}  # Single edge-case anomaly

        # Spread vehicles along primary corridor roads (ROAD_01, ROAD_02, ROAD_03, ROAD_04, ROAD_06)
        primary_roads = ["ROAD_01", "ROAD_02", "ROAD_03", "ROAD_04", "ROAD_06", "ROAD_07"]

        for i in range(1, vehicle_count + 1):
            vid = f"V{i:03d}"
            road_id = primary_roads[(i - 1) % len(primary_roads)]
            road_spec = next(r for r in roads_data if r["road_id"] == road_id)

            # Interpolate coordinates along the road segment
            fraction = round(0.08 + (0.84 * ((i * 7) % 19) / 19.0), 3)
            base_lat = road_spec["start_lat"] + fraction * (road_spec["end_lat"] - road_spec["start_lat"])
            base_lon = road_spec["start_lon"] + fraction * (road_spec["end_lon"] - road_spec["start_lon"])

            # Lane offset: Lane 1 (Left), Lane 2 (Center - corridor target), Lane 3 (Right)
            lane = (i % 3) + 1

            # Determine anomaly flags
            is_suspicious = (i in suspicious_indices)
            is_non_compliant = (i in low_compliance_indices)

            # Telemetry features
            if is_suspicious:
                speed = 125.0 if i % 2 == 0 else 4.0  # Abnormal speed
                accel = 6.8 if i % 2 == 0 else -7.2   # Impossible acceleration
                pos_consistency = round(random.uniform(0.15, 0.38), 2)
                mov_consistency = round(random.uniform(0.20, 0.40), 2)
                freshness = round(random.uniform(0.10, 0.35), 2)
                sensor_consistency = round(random.uniform(0.18, 0.42), 2)
                hist_trust = round(random.uniform(0.25, 0.45), 2)
            else:
                speed = round(random.uniform(32.0, 54.0), 1)
                accel = round(random.uniform(-1.2, 1.4), 2)
                pos_consistency = round(random.uniform(0.85, 0.98), 2)
                mov_consistency = round(random.uniform(0.82, 0.97), 2)
                freshness = round(random.uniform(0.90, 0.99), 2)
                sensor_consistency = round(random.uniform(0.88, 0.99), 2)
                hist_trust = round(random.uniform(0.80, 0.96), 2)

            vehicle = {
                "vehicle_id": vid,
                "latitude": round(base_lat, 6),
                "longitude": round(base_lon, 6),
                "speed": speed,
                "acceleration": accel,
                "heading": 48.0 + random.uniform(-4.0, 4.0),
                "current_lane": lane,
                "vehicle_type": random.choice(vehicle_types),
                "movement_direction": road_spec["road_direction"],
                "destination": road_spec["end_intersection"],
                "driver_id": f"DRV_{i:03d}",
                "road_id": road_id,
                "distance_along_road": round(fraction * road_spec["length_meters"], 1)
            }
            normal_vehicles.append(vehicle)

            # Driver Behaviour
            if is_non_compliant:
                yielding_status = "NON_YIELDING"
                resp_time = round(random.uniform(7.5, 12.0), 2)
                prev_actions = random.randint(0, 1)
                comp_label = "Low"
            else:
                yielding_status = "YIELDING" if lane == 2 else "MAINTAINING"
                resp_time = round(random.uniform(1.2, 3.2), 2)
                prev_actions = random.randint(4, 10)
                comp_label = "High" if resp_time < 2.5 else "Medium"

            behaviour = {
                "vehicle_id": vid,
                "previous_yielding_actions": prev_actions,
                "current_yielding_status": yielding_status,
                "response_time": resp_time,
                "lane_change_history": [f"Lane {lane} -> Lane {max(1, lane - 1)}", f"Lane {lane}"],
                "acceleration_history": [round(accel + random.uniform(-0.3, 0.3), 2) for _ in range(5)],
                "driver_compliance_label": comp_label
            }
            driver_behaviours.append(behaviour)

            # Trust Profile
            trust_info = {
                "vehicle_id": vid,
                "position_consistency": pos_consistency,
                "movement_consistency": mov_consistency,
                "message_freshness": freshness,
                "sensor_consistency": sensor_consistency,
                "historical_trust_score": hist_trust
            }
            trust_records.append(trust_info)

            # Generate initial authenticated V2X telemetry beacon
            # Pre-register vehicle keys
            v2x_security.get_or_create_vehicle_keys(vid, role="NORMAL_VEHICLE")
            beacon_payload = {
                "sender_id": vid,
                "receiver_id": "BROADCAST",
                "message_type": "TELEMETRY_BEACON",
                "timestamp": now - random.uniform(0.1, 2.0) if not is_suspicious else now - 35.0,
                "sequence_number": i * 10 + 1,
                "message_content": {
                    "latitude": vehicle["latitude"],
                    "longitude": vehicle["longitude"],
                    "speed": vehicle["speed"],
                    "lane": vehicle["current_lane"],
                    "heading": vehicle["heading"]
                }
            }
            # Sign if legitimate, or forge if suspicious
            if is_suspicious and i % 2 == 1:
                # Corrupt signature to demonstrate detection
                signed_beacon = dict(beacon_payload)
                signed_beacon["signature_hex"] = "badc0ffee000deadbeef1234567890abcdef"
                signed_beacon["signature_status"] = "CORRUPTED"
            else:
                signed_beacon = v2x_security.sign_message(vid, beacon_payload)
            v2x_messages.append(signed_beacon)

        # Emergency vehicle announcement message
        v2x_security.get_or_create_vehicle_keys("EV01", role="EMERGENCY_VEHICLE")
        ev_announcement = {
            "sender_id": "EV01",
            "receiver_id": "BROADCAST",
            "message_type": "EMERGENCY_ANNOUNCEMENT",
            "timestamp": now,
            "sequence_number": 1,
            "message_content": {
                "emergency_vehicle_id": "EV01",
                "priority_level": 1,
                "target_lane": 2,
                "intended_route": emergency_vehicle["intended_route"],
                "destination": emergency_vehicle["destination"],
                "estimated_speed": emergency_vehicle["speed"]
            }
        }
        signed_ev_msg = v2x_security.sign_message("EV01", ev_announcement)
        v2x_messages.insert(0, signed_ev_msg)

        # Save to disk
        self._save_json("roads.json", roads_data)
        self._save_json("emergency_vehicles.json", [emergency_vehicle])
        self._save_json("vehicles.json", normal_vehicles)
        self._save_json("driver_behaviour.json", driver_behaviours)
        self._save_json("trust_data.json", trust_records)
        self._save_json("communication.json", v2x_messages)

        return {
            "scenario": scenario_type,
            "vehicle_count": len(normal_vehicles),
            "emergency_vehicles": [emergency_vehicle],
            "roads_count": len(roads_data),
            "messages_count": len(v2x_messages)
        }

    def _save_json(self, filename: str, data: Any):
        filepath = DATA_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


scenario_gen = ScenarioGenerator()

