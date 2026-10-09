"""Opt-in Zenoh event transport: signed data only, no remote command execution.

Zenoh is pub/sub/query middleware, not "OSI layer 2" or intrinsically
zero-overhead. Configure encryption, peer ACLs and identity outside this code.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import re
import secrets
import time


class MeshError(ValueError):
    pass


ALLOWED_TYPES = frozenset({"telemetry", "state", "status"})
KEY = re.compile(r"^omega/edge/(?:telemetry|state|status)/[A-Za-z0-9_-]{1,64}$")
MAX_BYTES = 8192
MAX_SKEW = 300


def _secret(secret):
    if not isinstance(secret, bytes) or len(secret)<32:
        raise MeshError("HMAC secret must be >=32 bytes, private and out of the repository")
    return secret


def _json(value):
    try:
        raw=json.dumps(value,sort_keys=True,separators=(",",":"),
                       ensure_ascii=False,allow_nan=False).encode("utf-8")
    except (TypeError,ValueError) as exc:
        raise MeshError("Event contains invalid or non-JSON data") from exc
    if len(raw)>MAX_BYTES:
        raise MeshError("Signed event size exceeds 8192 bytes")
    return raw


def sign_event(key,kind,payload,secret,*,nonce=None,timestamp=None):
    """Create HMAC-signed telemetry only; key and action type are allowlisted."""
    _secret(secret)
    if not isinstance(key,str) or KEY.fullmatch(key) is None:
        raise MeshError("Key not in allowed omega/edge/<type>/<node> namespace")
    if kind not in ALLOWED_TYPES or key.split("/")[2]!=kind:
        raise MeshError("Event kind inconsistent with topic")
    if timestamp is None:
        timestamp=int(time.time())
    if type(timestamp) is not int or timestamp<0:
        raise MeshError("Invalid timestamp")
    if nonce is None:
        nonce=secrets.token_hex(16)
    if not isinstance(nonce,str) or re.fullmatch(r"[a-f0-9]{32}",nonce) is None:
        raise MeshError("Nonce must be exactly 128-bit lowercase hex")
    body={"schema_version":1,"key":key,"type":kind,
          "nonce":nonce,"timestamp":timestamp,"payload":payload}
    raw=_json(body)
    body["signature"]=hmac.new(secret,raw,hashlib.sha256).hexdigest()
    _json(body)
    return body


class ReplayGuard:
    """In-process replay filter; for distributed systems use durable nonce storage."""

    def __init__(self,max_entries=10000):
        if type(max_entries) is not int or not 1<=max_entries<=100000:
            raise MeshError("Invalid replay budget")
        self._used={}
        self.max_entries=max_entries

    def register(self,nonce,now):
        self._used={n:t for n,t in self._used.items() if now-t<=MAX_SKEW*2}
        if nonce in self._used:
            raise MeshError("Replay detected")
        if len(self._used)>=self.max_entries:
            raise MeshError("Replay store full: fail closed")
        self._used[nonce]=now


def verify_event(event,secret,*,now=None,replays=None,expected_key=None):
    """Validate signature, staleness, allowlists and optional nonce reuse."""
    _secret(secret)
    if not isinstance(event,dict) or set(event)!={"schema_version","key","type","nonce","timestamp","payload","signature"}:
        raise MeshError("Invalid signed event schema")
    if type(event["schema_version"]) is not int or event["schema_version"]!=1:
        raise MeshError("Unsupported schema")
    key=event["key"];kind=event["type"]
    if not isinstance(key,str) or KEY.fullmatch(key) is None or kind not in ALLOWED_TYPES or key.split("/")[2]!=kind:
        raise MeshError("Untrusted topic or kind")
    if expected_key is not None and key!=expected_key:
        raise MeshError("Topic mismatch")
    nonce=event["nonce"]
    if not isinstance(nonce,str) or re.fullmatch(r"[a-f0-9]{32}",nonce) is None:
        raise MeshError("Malformed nonce")
    timestamp=event["timestamp"]
    if type(timestamp) is not int or timestamp<0:
        raise MeshError("Invalid timestamp")
    if now is None:
        now=int(time.time())
    if type(now) is not int or abs(timestamp-now)>MAX_SKEW:
        raise MeshError("Expired or future-dated message")
    signature=event["signature"]
    if not isinstance(signature,str) or re.fullmatch(r"[a-f0-9]{64}",signature) is None:
        raise MeshError("Malformed signature")
    data={key:value for key,value in event.items() if key!="signature"}
    correct=hmac.new(secret,_json(data),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(correct,signature):
        raise MeshError("Event HMAC mismatch")
    if replays is not None:
        if not isinstance(replays,ReplayGuard):
            raise MeshError("Invalid replay registry")
        replays.register(nonce,now)
    return {"authenticated_by":"shared_secret_hmac",
            "key":key,"type":kind,"payload":event["payload"],
            "side_effects":False}


def encode_event(event):
    return _json(event).decode("utf-8")


def decode_event(raw):
    if not isinstance(raw,str) or len(raw.encode("utf-8"))>MAX_BYTES:
        raise MeshError("Bad event encoding size")
    try:
        obj=json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MeshError("Invalid event JSON") from exc
    if not isinstance(obj,dict):
        raise MeshError("Expected JSON object")
    return obj


def zenoh_publish(event,secret,*,permit_network=False,config=None):
    """Strictly explicit network opt-in; verifies event before opening Zenoh."""
    verify_event(event,secret)
    if permit_network is not True:
        raise MeshError("Network disabled unless permit_network=True explicitly")
    try:
        import zenoh
    except ImportError as exc:
        raise MeshError("Install optional dependency: pip install '.[mesh]'") from exc
    with zenoh.open(config if config is not None else zenoh.Config()) as session:
        session.put(event["key"],encode_event(event))
    return {"published":True,"key":event["key"],"transport":"zenoh",
            "peer_authenticated":False,"note":"Provision Zenoh transport identity/ACL externally"}


def zenoh_listen(key,secret,*,duration_seconds=1,permit_network=False,config=None):
    """Collect signed events for a bounded interval. No callback executes commands."""
    _secret(secret)
    if not isinstance(key,str) or KEY.fullmatch(key) is None:
        raise MeshError("Subscriber key must be a specific allowlisted topic")
    if type(duration_seconds) not in (int,float) or not 0<duration_seconds<=60:
        raise MeshError("Listen duration must be (0,60] seconds")
    if permit_network is not True:
        raise MeshError("Network disabled unless permit_network=True explicitly")
    try:
        import zenoh
    except ImportError as exc:
        raise MeshError("Install optional dependency: pip install '.[mesh]'") from exc
    seen=ReplayGuard()
    events=[]
    def on_sample(sample):
        try:
            raw=sample.payload.to_string()
            msg=verify_event(decode_event(raw),secret,replays=seen,expected_key=key)
            if len(events)<1000:
                events.append(msg)
        except MeshError:
            pass   # Invalid remote message is dropped, never executed.
    with zenoh.open(config if config is not None else zenoh.Config()) as session:
        with session.declare_subscriber(key,on_sample):
            time.sleep(duration_seconds)
    return events
