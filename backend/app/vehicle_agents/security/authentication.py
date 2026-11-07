import json
import time
from typing import Dict, Any, Tuple, Optional
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature
from app.vehicle_agents.security.identity import AgentIdentity


class AgentAuthenticator:
    """
    Implements Formula 3 from the research paper:
    sigma_i = Sign_sk_i(H(m_i))
    
    Provides:
    - ECDSA NIST P-256 digital signature generation & verification
    - SHA-256 deterministic payload hashing
    - Timestamp freshness checks (<= 15.0s window)
    - Monotonic sequence number tracking per peer to reject replay attacks
    - Independent security event auditing
    """

    def __init__(self, identity: AgentIdentity, max_age_seconds: float = 15.0):
        self.identity = identity
        self.max_age_seconds = max_age_seconds
        # sender_id -> last_seen_sequence_number
        self.peer_sequence_tracker: Dict[str, int] = {}
        # sender_id -> peer_public_key (ec.EllipticCurvePublicKey)
        self.peer_public_keys: Dict[str, ec.EllipticCurvePublicKey] = {}
        # Auditable local security log for this specific agent
        self.security_log: list = []

    def canonicalize(self, message: Dict[str, Any]) -> bytes:
        """
        Creates deterministic canonical byte stream for SHA-256 hashing.
        Excludes signature and public key fields to ensure symmetry.
        """
        excluded = {"signature_hex", "signature_status", "public_key_pem"}
        filtered = {k: v for k, v in message.items() if k not in excluded}
        return json.dumps(filtered, sort_keys=True, separators=(',', ':')).encode('utf-8')

    def sign_message(self, message_dict: Dict[str, Any], sequence_number: int) -> Dict[str, Any]:
        """
        Applies sigma_i = Sign_sk_i(H(m_i)) using agent's private key.
        """
        msg = dict(message_dict)
        msg["sender_id"] = self.identity.vehicle_id
        msg["timestamp"] = time.time()
        msg["sequence_number"] = sequence_number
        msg["public_key_pem"] = self.identity.public_pem

        data_bytes = self.canonicalize(msg)
        signature = self.identity.private_key.sign(
            data_bytes,
            ec.ECDSA(hashes.SHA256())
        )

        msg["signature_hex"] = signature.hex()
        msg["signature_status"] = "VALID_SIGNATURE"
        return msg

    def register_peer_key(self, sender_id: str, public_key_pem: str):
        try:
            pub_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
            self.peer_public_keys[sender_id] = pub_key
        except Exception as e:
            self._log_event(sender_id, "KEY_REGISTRATION_FAILED", f"Error loading PEM: {e}")

    def verify_message(self, message: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates:
        1. Timestamp freshness
        2. Sequence number progression (replay prevention)
        3. ECDSA SHA-256 digital signature
        """
        sender_id = message.get("sender_id")
        seq = message.get("sequence_number", 0)
        timestamp = message.get("timestamp", 0.0)
        sig_hex = message.get("signature_hex")
        pem = message.get("public_key_pem")

        if not sender_id:
            return False, "Missing sender_id"

        # 1. Freshness Check
        now = time.time()
        age = abs(now - timestamp)
        if age > self.max_age_seconds:
            reason = f"Stale message rejected: age {age:.2f}s > {self.max_age_seconds}s"
            self._log_event(sender_id, "FRESHNESS_REJECTED", reason)
            return False, reason

        # 2. Sequence Number Replay Check
        last_seq = self.peer_sequence_tracker.get(sender_id, -1)
        if seq <= last_seq:
            reason = f"Replay attack rejected: sequence {seq} <= last seen {last_seq}"
            self._log_event(sender_id, "REPLAY_REJECTED", reason)
            return False, reason

        # 3. Signature Verification
        if not sig_hex:
            reason = "Unsigned message rejected"
            self._log_event(sender_id, "UNSIGNED_REJECTED", reason)
            return False, reason

        # Ensure public key is loaded
        if sender_id not in self.peer_public_keys and pem:
            self.register_peer_key(sender_id, pem)

        pub_key = self.peer_public_keys.get(sender_id)
        if not pub_key:
            reason = f"Public key not available for sender {sender_id}"
            self._log_event(sender_id, "MISSING_KEY_REJECTED", reason)
            return False, reason

        try:
            sig_bytes = bytes.fromhex(sig_hex)
            data_bytes = self.canonicalize(message)
            pub_key.verify(sig_bytes, data_bytes, ec.ECDSA(hashes.SHA256()))
        except (InvalidSignature, ValueError) as e:
            reason = f"Cryptographic signature verification failed: {e}"
            self._log_event(sender_id, "SIGNATURE_INVALID", reason)
            return False, reason

        # Record sequence upon valid receipt
        self.peer_sequence_tracker[sender_id] = seq
        self._log_event(sender_id, "AUTHENTICATED", f"Message seq #{seq} authenticated via ECDSA-SHA256")
        return True, "Valid authenticated message"

    def _log_event(self, peer_id: str, event_type: str, details: str):
        event = {
            "timestamp": time.time(),
            "peer_id": peer_id,
            "event_type": event_type,
            "details": details
        }
        self.security_log.append(event)
        if len(self.security_log) > 100:
            self.security_log.pop(0)

