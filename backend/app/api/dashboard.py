from fastapi import APIRouter
from app.core.corridor_manager import corridor_manager


router = APIRouter(prefix="/api/dashboard", tags=["Executive Dashboard"])


@router.get("/summary")
def get_dashboard_summary():
    status = corridor_manager.get_corridor_status()

    # Aggregate trust counts
    high_trust = sum(1 for t in corridor_manager.trust_evaluations.values() if t.get("trust_category") == "High")
    med_trust = sum(1 for t in corridor_manager.trust_evaluations.values() if t.get("trust_category") == "Medium")
    susp_trust = sum(1 for t in corridor_manager.trust_evaluations.values() if t.get("trust_category") == "Suspicious")

    # Aggregate compliance counts
    high_comp = sum(1 for c in corridor_manager.compliance_predictions.values() if c.get("compliance_class") == "High")
    med_comp = sum(1 for c in corridor_manager.compliance_predictions.values() if c.get("compliance_class") == "Medium")
    low_comp = sum(1 for c in corridor_manager.compliance_predictions.values() if c.get("compliance_class") == "Low")

    # Trust distribution data for charts
    trust_chart = [
        {"name": "High Trust (≥0.75)", "count": high_trust, "fill": "#10b981"},
        {"name": "Medium Trust (0.45-0.75)", "count": med_trust, "fill": "#f59e0b"},
        {"name": "Suspicious / Anomalies (<0.45)", "count": susp_trust, "fill": "#ef4444"}
    ]

    # Compliance distribution data for charts
    compliance_chart = [
        {"name": "High Compliance", "count": high_comp, "fill": "#06b6d4"},
        {"name": "Medium Compliance", "count": med_comp, "fill": "#8b5cf6"},
        {"name": "Low Compliance", "count": low_comp, "fill": "#f43f5e"}
    ]

    return {
        "status": "success",
        "kpis": {
            "total_vehicles": status["total_vehicles"],
            "active_emergency_vehicles": 1 if corridor_manager.emergency_vehicle else 0,
            "participating_coordination": status["participating_vehicle_count"],
            "high_trust_vehicles": high_trust,
            "suspicious_vehicles": susp_trust,
            "high_compliance_vehicles": high_comp,
            "low_compliance_vehicles": low_comp,
            "corridor_status": status["status"],
            "average_delay_seconds": status["average_delay_seconds"],
            "establishment_time_seconds": status["corridor_establishment_time_seconds"],
            "active_scenario": status["active_scenario"],
            "emergency_vehicle_speed": corridor_manager.emergency_vehicle.get("speed", 62.5),
            "emergency_destination": corridor_manager.emergency_vehicle.get("destination", "INT_5")
        },
        "charts": {
            "trust_distribution": trust_chart,
            "compliance_distribution": compliance_chart
        },
        "recent_events": status["recent_events"][:12]
    }


@router.get("/events")
def get_dashboard_events():
    return {
        "status": "success",
        "events": corridor_manager.events_log[:50]
    }


@router.get("/metrics")
def get_dashboard_metrics():
    return {
        "status": "success",
        "corridor_status": corridor_manager.get_corridor_status()
    }

