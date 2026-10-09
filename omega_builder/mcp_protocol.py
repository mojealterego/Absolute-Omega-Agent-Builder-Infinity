"""Offline MCP 2026-07-28 read-only envelope builder; no network transport."""
from __future__ import annotations
import json

class ProtocolError(ValueError):
    pass

READ_METHODS=frozenset(("server/discover","tools/list","prompts/list","resources/list"))
VERSION="2026-07-28"

def read_request(method,request_id,cursor=None):
    """Prepare stateless request. Never allow tools/call or side effects."""
    if method not in READ_METHODS:
        raise ProtocolError("Read-only methods only")
    if type(request_id) is not int or not 1<=request_id<2**31:
        raise ProtocolError("Invalid request identifier")
    if cursor is not None and (method=="server/discover" or not isinstance(cursor,str) or not 1<=len(cursor)<=2048):
        raise ProtocolError("Invalid pagination cursor")
    params={"_meta":{
        "io.modelcontextprotocol/protocolVersion":VERSION,
        "io.modelcontextprotocol/clientInfo":{"name":"omega-builder","version":"0.2.0"},
        "io.modelcontextprotocol/clientCapabilities":{}
    }}
    if cursor is not None:
        params["cursor"]=cursor
    body={"jsonrpc":"2.0","id":request_id,"method":method,"params":params}
    if len(json.dumps(body))>65536:
        raise ProtocolError("Oversized request")
    return {"http_method":"POST","headers":{
        "Content-Type":"application/json",
        "MCP-Protocol-Version":VERSION,
        "Mcp-Method":method},"body":body,
        "network":"DISABLED","executed":False}

def inspect_result(request,response):
    """Validate JSON-RPC correlation and listing shape, not server honesty."""
    if not isinstance(request,dict) or request.get("network")!="DISABLED":
        raise ProtocolError("Only offline request plans supported")
    if not isinstance(response,dict) or response.get("jsonrpc")!="2.0":
        raise ProtocolError("Malformed JSON-RPC response")
    body=request.get("body")
    if not isinstance(body,dict) or body.get("method") not in READ_METHODS:
        raise ProtocolError("Request was not allowlisted")
    if type(response.get("id")) is not int or response["id"]!=body.get("id"):
        raise ProtocolError("Mismatched request ID")
    if ("result" in response)==("error" in response):
        raise ProtocolError("Response requires exactly result or error")
    if "error" in response:
        return {"status":"REMOTE_ERROR","executed":False}
    result=response["result"]
    if not isinstance(result,dict) or result.get("resultType")!="complete":
        raise ProtocolError("Unsupported result or user interaction required")
    item_type={"tools/list":"tools","resources/list":"resources",
               "prompts/list":"prompts"}.get(body["method"])
    if item_type:
        items=result.get(item_type)
        if not isinstance(items,list) or len(items)>1000 or not all(isinstance(x,dict) for x in items):
            raise ProtocolError("Invalid listing")
    elif VERSION not in result.get("supportedVersions",[]):
        raise ProtocolError("Unsupported protocol revision")
    return {"status":"UNTRUSTED_METADATA","method":body["method"],
            "executed":False}
