import time
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


class AgentIdentity:
    """
    Manages an independent vehicle agent's cryptographic identity using ECDSA SECP256R1 (NIST P-256).
    Every vehicle agent instantiates its own AgentIdentity with its own private/public key pair.
    """

    def __init__(self, vehicle_id: str, role: str = "NORMAL_VEHICLE"):
        self.vehicle_id = vehicle_id
        self.role = role
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()

        self.public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        self.certificate = {
            "cert_id": f"CERT-{vehicle_id}-{int(time.time() * 1000)}",
            "vehicle_id": vehicle_id,
            "role": role,
            "algorithm": "ECDSA_SECP256R1_SHA256",
            "issuer": "SwarmTwin-V2X-Root-CA",
            "valid_from": time.time() - 3600,
            "valid_to": time.time() + 86400 * 365,
            "public_key_pem": self.public_pem
        }

    @property
    def public_key_pem(self) -> str:
        return self.public_pem

    def get_public_certificate(self) -> Dict[str, Any]:
        return dict(self.certificate)

