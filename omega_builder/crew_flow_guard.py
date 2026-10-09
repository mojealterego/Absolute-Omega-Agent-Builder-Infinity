"""CrewAI-inspired bounded Flow control: offline library, no agent execution."""
from dataclasses import dataclass
from hashlib import sha256
import json
import re

class FlowPolicyError(ValueError): pass
IDENT=re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")

def _id(value):
    if not isinstance(value,str) or IDENT.fullmatch(value) is None:
        raise FlowPolicyError("Invalid identifier")
    return value

def _integer(value,lo,hi):
    if type(value) is not int or not lo<=value<=hi:
        raise FlowPolicyError("Integer outside configured bounds")
    return value

def _json_bytes(value):
    try:
        raw=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()
    except (TypeError,ValueError) as exc:
        raise FlowPolicyError("Expected finite JSON input") from exc
    if len(raw)>65536:
        raise FlowPolicyError("JSON input exceeds 64KiB")
    return raw

def argument_sha256(arguments):
    if not isinstance(arguments,dict): raise FlowPolicyError("Tool arguments must be object")
    return sha256(_json_bytes(arguments)).hexdigest()

@dataclass(frozen=True)
class Step:
    name:str
    next_ok:str|None
    next_error:str|None
    max_attempts:int=1
    tools:tuple[str,...]=()

    def __post_init__(self):
        _id(self.name)
        for node in (self.next_ok,self.next_error):
            if node is not None: _id(node)
        _integer(self.max_attempts,1,10)
        if not isinstance(self.tools,tuple) or len(self.tools)>16 or len(self.tools)!=len(set(self.tools)):
            raise FlowPolicyError("Invalid tool allowlist")
        for tool in self.tools: _id(tool)

class FlowPolicy:
    def __init__(self,steps,start,max_events=100,max_cost_micro_usd=100000):
        if not isinstance(steps,(tuple,list)) or not 1<=len(steps)<=64 or any(not isinstance(s,Step) for s in steps):
            raise FlowPolicyError("Expected 1..64 typed steps")
        _id(start)
        self.steps={s.name:s for s in steps}
        if len(self.steps)!=len(steps) or start not in self.steps:
            raise FlowPolicyError("Unknown start or duplicate step")
        self.start=start
        self.max_events=_integer(max_events,1,10000)
        self.max_cost_micro_usd=_integer(max_cost_micro_usd,0,1000000000)
        visited=set();active=set()
        def visit(n):
            if n in active: raise FlowPolicyError("Cyclic Flow: only bounded retries supported")
            if n in visited: return
            active.add(n)
            for next_name in (self.steps[n].next_ok,self.steps[n].next_error):
                if next_name is not None:
                    if next_name not in self.steps: raise FlowPolicyError("Dangling edge")
                    visit(next_name)
            active.remove(n);visited.add(n)
        visit(start)
        if len(visited)!=len(self.steps): raise FlowPolicyError("Unreachable step")

class OfflineFlow:
    def __init__(self,policy):
        if not isinstance(policy,FlowPolicy): raise FlowPolicyError("Validated policy required")
        self.policy=policy
        self.current=policy.start
        self.attempts={}
        self.receipts=set()
        self.audit=[]
        self._last_digest="0"*64
        self.spent=0
        self.status="READY"

    def record(self,step,succeeded,observed_cost_micro_usd,receipt_id):
        if self.status!="READY" or step!=self.current: raise FlowPolicyError("Unexpected step/state")
        if type(succeeded) is not bool: raise FlowPolicyError("Success must be explicit bool")
        cost=_integer(observed_cost_micro_usd,0,1000000000)
        _id(receipt_id)
        if receipt_id in self.receipts: raise FlowPolicyError("Duplicate receipt")
        if len(self.audit)>=self.policy.max_events or cost+self.spent>self.policy.max_cost_micro_usd:
            self.status="BLOCKED_BUDGET"
            return self.snapshot()
        self.receipts.add(receipt_id);self.spent+=cost
        attempts=self.attempts.get(step,0)+1
        self.attempts[step]=attempts
        item=self.policy.steps[step]
        if succeeded:
            nxt=item.next_ok
            self.status="COMPLETE" if nxt is None else "READY"
        elif attempts<item.max_attempts:
            nxt=step
        else:
            nxt=item.next_error
            self.status="FAILED" if nxt is None else "READY"
        event={"step":step,"attempt":attempts,"receipt":receipt_id,
               "succeeded":succeeded,"cost_micro_usd":cost,"next":nxt}
        self.audit.append(event)
        # Hash chain is bounded per event; only tamper-evident if the final
        # digest is independently secured outside the process.
        self._last_digest=sha256(self._last_digest.encode()+_json_bytes(event)).hexdigest()
        self.current=nxt
        return self.snapshot()

    def snapshot(self):
        return {"status":self.status,"current":self.current,"events":len(self.audit),
                "spent_micro_usd":self.spent,
                "audit_sha256":self._last_digest,
                "executed_by_library":False}

def tool_intent(policy,step,tool,args,readonly=True,approved_sha256=None):
    """Check a tool intent only; human identity and runtime calls are NOT verified."""
    if not isinstance(policy,FlowPolicy) or step not in policy.steps:
        raise FlowPolicyError("Unknown step")
    _id(tool)
    if type(readonly) is not bool: raise FlowPolicyError("readonly must be boolean")
    digest=argument_sha256(args)
    allowed=tool in policy.steps[step].tools and (readonly or approved_sha256==digest)
    return {"eligible_for_separate_executor":allowed,"argument_sha256":digest,
            "identity_verified":False,"executed":False}


def replay_flow(policy, events):
    """Recompute event-chain state offline and reject tampered event receipts."""
    if not isinstance(policy,FlowPolicy) or not isinstance(events,(list,tuple)) or len(events)>policy.max_events:
        raise FlowPolicyError("Invalid bounded replay input")
    state=OfflineFlow(policy)
    required={"step","attempt","receipt","succeeded","cost_micro_usd","next"}
    for event in events:
        if not isinstance(event,dict) or set(event)!=required:
            raise FlowPolicyError("Malformed audit event")
        result=state.record(event["step"],event["succeeded"],event["cost_micro_usd"],event["receipt"])
        if result["status"]=="BLOCKED_BUDGET" or not state.audit or state.audit[-1]!=event:
            raise FlowPolicyError("Audit event disagrees with flow policy")
    return state.snapshot()
