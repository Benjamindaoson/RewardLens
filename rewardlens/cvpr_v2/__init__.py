"""CVPR-oriented counterfactual audit prototype (no model inference bundled)."""

from .metrics import audit_summary, matched_pairs, shared_support_gaps
from .protocol import ProtocolError, validate_records

__all__ = ["ProtocolError", "validate_records", "audit_summary", "matched_pairs", "shared_support_gaps"]
