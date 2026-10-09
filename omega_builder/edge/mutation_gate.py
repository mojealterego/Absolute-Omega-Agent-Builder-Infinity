"""Evidence-only signature gate for candidate changes; NEVER executes mutations.

An HMAC approval binds all recorded candidate claims, but does NOT magically
attest alignment, guarantee human review, or verify the tests were actually run.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import hmac
import json
import re


class GateError(ValueError):
    pass


HEX_SHA = re.compile(r"^[0-9a-f]{64}$")
CANDIDATE_KINDS = frozenset({"source_patch","config_change","model_weight_update"})


def _candidate(candidate):
    required={"candidate_id","candidate_kind","artifact_sha256","baseline_sha256",
              "alignment_score","human_safety_flag","tests_passed","security_scan_passed"}
    if not isinstance(candidate,dict) or set(candidate)!=required:
        raise GateError("Candidate manifest keys missing or unexpected")
    for key in ("candidate_id","candidate_kind"):
        if not isinstance(candidate[key],str) or not candidate[key] or len(candidate[key])>128:
            raise GateError("Invalid candidate identifier/type")
    if candidate["candidate_kind"] not in CANDIDATE_KINDS:
        raise GateError("Candidate type not allowlisted")
    if any(not isinstance(candidate[key],str) or not HEX_SHA.fullmatch(candidate[key])
           for key in ("artifact_sha256","baseline_sha256")):
        raise GateError("Both SHA-256 identifiers must be lowercase hexadecimal")
    if type(candidate["alignment_score"]) is not int or not 0<=candidate["alignment_score"]<=100:
        raise GateError("Alignment score must be int 0..100")
    if any(type(candidate[key]) is not bool for key in ("human_safety_flag","tests_passed","security_scan_passed")):
        raise GateError("Evidence flags must be booleans")
    return candidate


def _canonical(candidate):
    _candidate(candidate)
    return json.dumps(candidate,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")


def sha256_bytes(artifact):
    if not isinstance(artifact,bytes):
        raise GateError("Artifact must be raw bytes")
    return sha256(artifact).hexdigest()


def sign_review(candidate,private_reviewer_key):
    """Called by independent reviewer, NEVER with a key stored in a repository."""
    if not isinstance(private_reviewer_key,bytes) or len(private_reviewer_key)<32:
        raise GateError("Reviewer HMAC key must be at least 32 bytes")
    return hmac.new(private_reviewer_key,_canonical(candidate),sha256).hexdigest()


def assess_candidate(candidate,review_signature,private_reviewer_key):
    """Read-only decision. External provenance of the score/tests is required."""
    _candidate(candidate)
    if not isinstance(private_reviewer_key,bytes) or len(private_reviewer_key)<32:
        raise GateError("Reviewer key invalid")
    if not isinstance(review_signature,str) or not HEX_SHA.fullmatch(review_signature):
        raise GateError("Invalid review signature")
    expected=sign_review(candidate,private_reviewer_key)
    signed=hmac.compare_digest(expected,review_signature)
    conditions=(candidate["human_safety_flag"] and candidate["alignment_score"]>=80
                and candidate["tests_passed"] and candidate["security_scan_passed"])
    if not signed:
        return {"status":"DENIED","reason":"review_signature_invalid","executed":False}
    if not conditions:
        return {"status":"DENIED","reason":"policy_condition_failed","executed":False}
    return {"status":"ELIGIBLE_FOR_SEPARATE_HUMAN_DEPLOYMENT",
            "reason":"review_signed_and_declared_conditions_passed",
            "candidate_id":candidate["candidate_id"],"executed":False,
            "limitations":"self-reported tests and alignment score require external independent audit"}
