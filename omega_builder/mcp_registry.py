"""Offline MCP Registry discovery, deduplication and explicit admission triage.

Registry metadata is *untrusted input*. This module never downloads,
installs, starts, authorizes, calls, or pays for MCP servers or their tools.
"""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import re
from urllib.parse import urlsplit

class MCPRegistryError(ValueError):
    pass

NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,150}/[A-Za-z0-9][A-Za-z0-9._/-]{0,150}$")
VERSION = re.compile(r"^[0-9][A-Za-z0-9.+_-]{0,100}$")
TOOL = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,100}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
EVIDENCE_FIELDS = (
    "publisher_identity_checked", "source_reviewed", "license_approved",
    "version_pinned", "security_scan_passed", "sandbox_isolation_checked",
    "permissions_scoped",
)
WEIGHTS = (15, 20, 10, 10, 20, 15, 10)


def _string(value, name, maximum=2048):
    if not isinstance(value, str) or not value or len(value)>maximum:
        raise MCPRegistryError(f"{name}: nonempty bounded string required")
    if any(ord(c)<32 for c in value):
        raise MCPRegistryError(f"{name}: control characters forbidden")
    return value


def public_https_url(url):
    """Conservative metadata URL filter; NO network I/O or DNS verification.

    DNS rebinding and remote URL redirects need independent runtime defenses.
    """
    _string(url, "URL", 2048)
    try:
        parsed=urlsplit(url)
        port=parsed.port
        host=parsed.hostname
    except ValueError as exc:
        raise MCPRegistryError("Malformed URL") from exc
    if (parsed.scheme!="https" or not host or parsed.username or parsed.password
            or parsed.fragment or "\\" in url or port not in (None,443)):
        raise MCPRegistryError("Only public HTTPS without credentials/fragment/custom ports")
    host=host.lower().rstrip(".")
    if host in ("localhost", "local") or host.endswith((".local", ".internal", ".localhost")):
        raise MCPRegistryError("Private hostname forbidden")
    try:
        addr=ipaddress.ip_address(host)
    except ValueError:
        if "." not in host or len(host)>253 or not re.fullmatch(r"[a-z0-9][a-z0-9.-]*[a-z0-9]",host):
            raise MCPRegistryError("Invalid public DNS name")
    else:
        if not addr.is_global:
            raise MCPRegistryError("Private or reserved IP forbidden")
    return url


def _packages(server):
    value=server.get("packages",[])
    if not isinstance(value,list) or len(value)>50:
        raise MCPRegistryError("packages must be a bounded array")
    out=[]
    for package in value:
        if not isinstance(package,dict):
            raise MCPRegistryError("Package object expected")
        typ=_string(package.get("registryType"),"registryType",64)
        identifier=_string(package.get("identifier"),"identifier",512)
        version=package.get("version")
        if version is not None and (not isinstance(version,str) or not VERSION.fullmatch(version)):
            raise MCPRegistryError("Package version must be fixed, no 'latest' or ranges")
        digest=package.get("fileSha256")
        if digest is not None and (not isinstance(digest,str) or not SHA.fullmatch(digest)):
            raise MCPRegistryError("Malformed package SHA-256")
        out.append({"registry_type":typ,"identifier":identifier,
                    "pinned_version":version,"digest_present":digest is not None})
    return out


def normalize_entry(entry, source="official_mcp_registry"):
    """Normalize official {server, _meta} records or standalone server.json.

    Input may include user/registry descriptions with hostile instructions:
    no instructions or commands are executed or put into an agent prompt.
    """
    if not isinstance(entry,dict):
        raise MCPRegistryError("Server entry must be an object")
    if "server" in entry:
        server=entry["server"]
        meta=entry.get("_meta",{})
    else:
        server=entry
        meta=entry.get("_meta",{})
    if not isinstance(server,dict) or not isinstance(meta,dict):
        raise MCPRegistryError("Malformed server/_meta")
    name=_string(server.get("name"),"name",305)
    if not NAME.fullmatch(name) or ".." in name:
        raise MCPRegistryError("Registry server name must be namespace/name")
    version=_string(server.get("version"),"version",101)
    if not VERSION.fullmatch(version) or version=="latest":
        raise MCPRegistryError("Server version must be explicit")
    source=_string(source,"source",128)
    description=server.get("description","")
    if not isinstance(description,str) or len(description)>4096:
        raise MCPRegistryError("Description must be bounded string")
    repo=server.get("repository")
    repository_url=None
    repository_id=None
    if repo is not None:
        if not isinstance(repo,dict):
            raise MCPRegistryError("repository must be object")
        repository_url=public_https_url(repo.get("url"))
        repository_id=repo.get("id")
        if repository_id is not None:
            _string(repository_id,"repository.id",128)
    remote=server.get("remotes",[])
    if not isinstance(remote,list) or len(remote)>20:
        raise MCPRegistryError("remotes must be bounded list")
    transports=[]
    for r in remote:
        if not isinstance(r,dict):
            raise MCPRegistryError("Invalid remote")
        url=public_https_url(r.get("url"))
        kind=_string(r.get("type"),"remote type",80)
        transports.append({"type":kind,"url":url})
    official_meta=meta.get("io.modelcontextprotocol.registry/official",{})
    if not isinstance(official_meta,dict):
        official_meta={}
    status=official_meta.get("status","unknown")
    if status not in ("active","deprecated","deleted","unknown"):
        status="unknown"
    packages=_packages(server)
    return {
        "id":name,"version":version,"source_registry":source,
        "repository_url":repository_url,"repository_id":repository_id,
        "description_present":bool(description.strip()),
        "package_count":len(packages),"packages":packages,
        "remote_endpoints":transports,"registry_status":status,
        "trust":"UNVERIFIED_CANDIDATE","executable":False,
        "requires_review":True,
    }


def ingest_page(page,source="official_mcp_registry"):
    """Read one official v0.1 Registry API page with opaque nextCursor.

    Caller must separately retrieve each page. Returning a cursor never
    implicitly fetches another page or authorizes an installation.
    """
    if not isinstance(page,dict):
        raise MCPRegistryError("Registry page must be an object")
    servers=page.get("servers")
    if not isinstance(servers,list) or len(servers)>500:
        raise MCPRegistryError("Expected 0..500 registry records")
    meta=page.get("metadata",{})
    if not isinstance(meta,dict):
        raise MCPRegistryError("Invalid metadata")
    cursor=meta.get("nextCursor")
    if cursor is not None and (not isinstance(cursor,str) or len(cursor)>2048):
        raise MCPRegistryError("Invalid opaque nextCursor")
    if cursor=="":
        cursor=None
    out=[]
    ids=set()
    for entry in servers:
        item=normalize_entry(entry,source)
        identity=(item["id"],item["version"])
        if identity in ids:
            raise MCPRegistryError("Duplicate server/version within page")
        ids.add(identity)
        out.append(item)
    return {"candidates":out,"page_size":len(out),
            "next_cursor":cursor,"execution":"DISABLED",
            "approval":"MANUAL_SECURITY_REVIEW_REQUIRED"}


def deduplicate_candidates(pages):
    """Merge pages by (server name, version) while detecting metadata drift."""
    if not isinstance(pages,list) or not 1<=len(pages)<=200:
        raise MCPRegistryError("Expected bounded list of normalized pages")
    found={}
    for page in pages:
        if not isinstance(page,dict) or not isinstance(page.get("candidates"),list):
            raise MCPRegistryError("Invalid normalized registry page")
        for item in page["candidates"]:
            if not isinstance(item,dict) or item.get("trust")!="UNVERIFIED_CANDIDATE":
                raise MCPRegistryError("Normalized candidate required")
            key=(item.get("id"),item.get("version"))
            if key in found and found[key]!=item:
                raise MCPRegistryError("Conflicting versions/metadata across pages")
            found[key]=item
            if len(found)>10000:
                raise MCPRegistryError("Candidate catalogue limit exceeded")
    return sorted(found.values(),key=lambda x:(x["id"],x["version"]))


def assess_candidate(candidate,evidence):
    """Conservative 7-factor *user-supplied* triage, not Top MCPs' scoring.

    A high numeric score NEVER causes installation or implicit permission.
    """
    if not isinstance(candidate,dict) or candidate.get("trust")!="UNVERIFIED_CANDIDATE":
        raise MCPRegistryError("Normalized candidate required")
    if not isinstance(evidence,dict) or set(evidence)!=set(EVIDENCE_FIELDS):
        raise MCPRegistryError("Seven explicitly named evidence fields required")
    if any(type(evidence[name]) is not bool for name in EVIDENCE_FIELDS):
        raise MCPRegistryError("Evidence fields must be booleans")
    score=sum(weight for name,weight in zip(EVIDENCE_FIELDS,WEIGHTS) if evidence[name])
    unverified=[name for name in EVIDENCE_FIELDS if not evidence[name]]
    status=candidate.get("registry_status")
    if status in ("deleted","deprecated"):
        status="BLOCKED_DEPRECATED_OR_DELETED"
    elif unverified:
        status="REVIEW_REQUIRED"
    else:
        status="REVIEW_REQUIRED_ALL_SELF_ATTESTED"
    return {"id":candidate["id"],"version":candidate["version"],
            "score_0_100":score,"missing_checks":unverified,"status":status,
            "scores_are":"CALLER_ASSERTED_UNVERIFIED",
            "approval":"EXPLICIT_HUMAN_APPROVAL_REQUIRED",
            "install_allowed":False,"execute_allowed":False,"payment_allowed":False}


def plan_tool_descriptors(manifest,allowlist,max_tools=8):
    """Dynamic-loading plan WITHOUT making tool calls or executing untrusted text.

    Tool lists from external servers are untrusted declarations, and may change
    between discovery and use. A real client must enforce scopes *at call time*.
    """
    if not isinstance(manifest,list) or len(manifest)>2000:
        raise MCPRegistryError("Bounded tool descriptor list expected")
    if not isinstance(allowlist,list) or len(allowlist)>100:
        raise MCPRegistryError("Explicit list of allowed tool names required")
    if any(not isinstance(name,str) or not TOOL.fullmatch(name) for name in allowlist):
        raise MCPRegistryError("Malformed allowlist tool identifier")
    if type(max_tools) is not int or not 1<=max_tools<=32:
        raise MCPRegistryError("Tool-load budget must be 1..32")
    wanted=set(allowlist)
    present=set()
    selected=[]
    for raw in manifest:
        if not isinstance(raw,dict):
            raise MCPRegistryError("Tool descriptor must be object")
        name=raw.get("name")
        if not isinstance(name,str) or not TOOL.fullmatch(name):
            raise MCPRegistryError("Invalid tool identifier")
        if name in present:
            raise MCPRegistryError("Duplicate tool names")
        present.add(name)
        if name not in wanted:
            continue
        schema=raw.get("inputSchema")
        if not isinstance(schema,dict) or schema.get("type")!="object":
            raise MCPRegistryError("Tool inputSchema must be JSON object schema")
        # Plain schema data, bounded before exposure; never interpreted as code.
        import json
        encoded=json.dumps(schema,ensure_ascii=False,allow_nan=False)
        if len(encoded)>16000:
            raise MCPRegistryError("Tool schema exceeds limit")
        description=raw.get("description","")
        if not isinstance(description,str):
            raise MCPRegistryError("Invalid description")
        selected.append({"name":name,"inputSchema":schema,
                         "description":description[:500],
                         "untrusted_description":True})
        if len(selected)>max_tools:
            raise MCPRegistryError("Tool budget exhausted")
    return {"descriptors":selected,
            "missing_tools":sorted(wanted-present),
            "selected_count":len(selected),
            "executed":False,"state":"SCHEMA_ONLY_NOT_AUTHORIZED"}
