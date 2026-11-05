from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from app.core.cryptography import v2x_security


router = APIRouter(prefix="/api/security", tags=["Security & V2X Authentication"])


class SignMessageRequest(BaseModel):
    vehicle_id: str
    message_content: Dict[str, Any]
    message_type: str = "TELEMETRY_BEACON"
    sequence_number: int = 1


class VerifyMessageRequest(BaseModel):
    message: Dict[str, Any]


@router.post("/sign-message")
def sign_message(req: SignMessageRequest):
    import time
    raw_msg = {
        "sender_id": req.vehicle_id,
        "receiver_id": "BROADCAST",
        "message_type": req.message_type,
        "timestamp": time.time(),
        "sequence_number": req.sequence_number,
        "message_content": req.message_content
    }
    signed = v2x_security.sign_message(req.vehicle_id, raw_msg)
    return {
        "status": "success",
        "signed_message": signed
    }


@router.post("/verify-message")
def verify_message(req: VerifyMessageRequest):
    is_valid, reason = v2x_security.verify_message(req.message)
    return {
        "status": "success",
        "is_valid": is_valid,
        "verification_result": "ACCEPTED" if is_valid else "REJECTED",
        "reason": reason,
        "message_id": f"{req.message.get('sender_id')}-{req.message.get('sequence_number')}"
    }


@router.get("/events")
def get_security_events(limit: int = 50):
    events = v2x_security.get_security_events(limit=limit)
    return {
        "status": "success",
        "total_events": len(events),
        "data": events
    }


@router.get("/keys")
def get_registered_keys():
    records = []
    for vid, data in v2x_security.vehicle_keys.items():
        records.append({
            "vehicle_id": vid,
            "role": data["certificate"].get("role"),
            "cert_id": data["certificate"].get("cert_id"),
            "algorithm": data["certificate"].get("algorithm"),
            "issuer": data["certificate"].get("issuer"),
            "public_key_pem": data["public_key_pem"][:90] + "..."
        })
    return {
        "status": "success",
        "total_keys": len(records),
        "data": records
    }

