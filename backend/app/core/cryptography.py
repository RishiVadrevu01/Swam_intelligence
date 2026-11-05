import time
import json
import hashlib
from typing import Dict, Tuple, Optional, Any
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.utils import (
    encode_dss_signature,
    decode_dss_signature
)
from cryptography.exceptions import InvalidSignature
from app.config import SECURITY_CONFIG


class V2XSecurityManager:
    """
    Manages ECDSA key pairs, certificate profiles, digital signatures,
    SHA-256 integrity hashing, timestamp validation, and sequence number replay detection.
    """
    def __init__(self):
        # vehicle_id -> {"private_key": ec.EllipticCurvePrivateKey, "public_key": ec.EllipticCurvePublicKey, "cert": dict}
        self.vehicle_keys: Dict[str, Dict[str, Any]] = {}
        # vehicle_id -> last_seen_sequence_number
        self.sequence_tracker: Dict[str, int] = {}
        # Log of security verification events
        self.security_events: list = []

    def get_or_create_vehicle_keys(self, vehicle_id: str, role: str = "NORMAL_VEHICLE") -> Dict[str, Any]:
        """
        Retrieves or generates an ECDSA key pair (SECP256R1) and synthetic certificate.
        """
        if vehicle_id in self.vehicle_keys:
            return self.vehicle_keys[vehicle_id]

        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        certificate = {
            "cert_id": f"CERT-V2X-{vehicle_id}-{int(time.time())}",
            "vehicle_id": vehicle_id,
            "role": role,
            "algorithm": "ECDSA_SECP256R1_SHA256",
            "issuer": "SYNTHETIC_V2X_ROOT_CA",
            "valid_from": time.time() - 3600,
            "valid_to": time.time() + 86400 * 365,
            "public_key_pem": public_pem
        }

        entry = {
            "private_key": private_key,
            "public_key": public_key,
            "public_key_pem": public_pem,
            "certificate": certificate
        }
        self.vehicle_keys[vehicle_id] = entry
        return entry

    def canonicalize_message(self, message_dict: Dict[str, Any]) -> bytes:
        """
        Produces deterministic SHA-256 hashable representation of message contents.
        """
        # Exclude signature and public key metadata fields
        exclude_fields = {"signature_hex", "signature_status", "public_key_pem"}
        filtered = {k: v for k, v in message_dict.items() if k not in exclude_fields}
        canonical_str = json.dumps(filtered, sort_keys=True, separators=(',', ':'))
        return canonical_str.encode('utf-8')

    def sign_message(self, vehicle_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Signs a message using the vehicle's ECDSA private key.
        """
        keys = self.get_or_create_vehicle_keys(vehicle_id)
        private_key = keys["private_key"]

        data_bytes = self.canonicalize_message(message)
        signature = private_key.sign(
            data_bytes,
            ec.ECDSA(hashes.SHA256())
        )

        signed_msg = dict(message)
        signed_msg["signature_hex"] = signature.hex()
        signed_msg["signature_status"] = "SIGNED"
        signed_msg["public_key_pem"] = keys["public_key_pem"]

        self._record_event(
            vehicle_id=vehicle_id,
            event_type="SIGNATURE_GENERATED",
            status="SUCCESS",
            details=f"Message {message.get('message_type', 'UNKNOWN')} seq #{message.get('sequence_number', 0)} signed."
        )
        return signed_msg

    def verify_message(self, message: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verifies ECDSA signature, message freshness, and sequence replay detection.
        """
        sender_id = message.get("sender_id")
        seq = message.get("sequence_number", 0)
        timestamp = message.get("timestamp", 0)
        sig_hex = message.get("signature_hex")

        if not sender_id:
            return False, "Missing sender_id in V2X message"

        # 1. Message Freshness Check
        now = time.time()
        time_diff = abs(now - timestamp)
        max_age = SECURITY_CONFIG["message_validity_window_seconds"]
        if time_diff > max_age:
            reason = f"Stale message rejected: age {time_diff:.2f}s exceeds limit {max_age}s"
            self._record_event(sender_id, "FRESHNESS_CHECK_FAILED", "REJECTED", reason)
            return False, reason

        # 2. Sequence Number Replay Check
        last_seq = self.sequence_tracker.get(sender_id, -1)
        if seq <= last_seq:
            reason = f"Replay attack detected: sequence {seq} <= last seen {last_seq}"
            self._record_event(sender_id, "REPLAY_ATTACK_DETECTED", "REJECTED", reason)
            return False, reason

        # 3. Signature Verification
        if not sig_hex:
            reason = "Unsigned message rejected: signature_hex is missing"
            self._record_event(sender_id, "MISSING_SIGNATURE", "REJECTED", reason)
            return False, reason

        keys = self.get_or_create_vehicle_keys(sender_id)
        public_key = keys["public_key"]

        try:
            sig_bytes = bytes.fromhex(sig_hex)
            data_bytes = self.canonicalize_message(message)
            public_key.verify(sig_bytes, data_bytes, ec.ECDSA(hashes.SHA256()))
        except (InvalidSignature, ValueError) as e:
            reason = f"Cryptographic signature verification failed: {str(e)}"
            self._record_event(sender_id, "INVALID_SIGNATURE", "REJECTED", reason)
            return False, reason

        # Update last seen sequence number upon successful verification
        self.sequence_tracker[sender_id] = seq
        self._record_event(
            sender_id,
            "MESSAGE_VERIFIED",
            "ACCEPTED",
            f"Message {message.get('message_type')} seq #{seq} authenticated via ECDSA-SHA256"
        )
        return True, "Valid and authenticated message"

    def _record_event(self, vehicle_id: str, event_type: str, status: str, details: str):
        event = {
            "timestamp": time.time(),
            "vehicle_id": vehicle_id,
            "event_type": event_type,
            "status": status,
            "details": details
        }
        self.security_events.append(event)
        if len(self.security_events) > 100:
            self.security_events.pop(0)

    def get_security_events(self, limit: int = 50):
        return sorted(self.security_events, key=lambda x: x["timestamp"], reverse=True)[:limit]


# Global singleton instance
v2x_security = V2XSecurityManager()
