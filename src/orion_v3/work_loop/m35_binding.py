"""Fail-closed exact-action manifest for the experimental native M3.5 child.

This validates the handoff contract; native enforcement is separately required.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import hmac

from .contracts import Proposal


@dataclass(frozen=True)
class FixedActionManifest:
    proposal_hash: str
    workspace: str
    target: str
    content_sha256: str
    source_revision: str

    def canonical_bytes(self) -> bytes:
        return json.dumps(self.__dict__, sort_keys=True, separators=(",", ":")).encode()


def bind_fixed_action(proposal: Proposal, revision: str) -> FixedActionManifest:
    root = Path(proposal.workspace).resolve(strict=True)
    if root.drive.upper() != "E:" or not root.name.startswith("ORION-M35-"):
        raise ValueError("disposable E: workspace required")
    target = root / "approved.txt"
    content = "ORION M35 approved fixture\n"
    if (proposal.operation != "filesystem.write" or
        set(proposal.args) != {"path", "content"} or
        proposal.args["path"] != str(target) or
        proposal.args["content"] != content or
        proposal.requested_network or proposal.requested_install or
        proposal.requested_system_change or not revision):
        raise ValueError("fixed-action proposal mismatch")
    return FixedActionManifest(proposal.proposal_hash, str(root), str(target),
                               hashlib.sha256(content.encode()).hexdigest(), revision)


def authenticate_manifest(manifest: FixedActionManifest, secret: bytes) -> str:
    """MAC the complete canonical manifest, not just its proposal hash."""
    if len(secret) < 32:
        raise ValueError("manifest key too short")
    return hmac.new(secret, manifest.canonical_bytes(), hashlib.sha256).hexdigest()


def verify_manifest_mac(manifest: FixedActionManifest, secret: bytes, mac: str) -> bool:
    if not isinstance(mac, str) or len(mac) != 64:
        return False
    return hmac.compare_digest(authenticate_manifest(manifest, secret), mac)
