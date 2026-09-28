#!/usr/bin/env python3
"""Small, dependency-free local AgentDesk MCP discovery experiment."""
import argparse
import json
import re
import sys
from pathlib import Path

CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text())
ALIASES = {
    "transcribe": "speech", "transcription": "speech", "audio": "speech",
    "recorded": "prerecorded", "pre-recorded": "prerecorded",
    "live": "streaming", "realtime": "streaming", "real-time": "streaming",
    "text": "text", "stt": "speech"
}
STOP = {"a", "an", "the", "to", "for", "of", "and", "service", "api", "find", "me", "under"}


def tokens(s):
    return {ALIASES.get(w, w) for w in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", s.lower()) if w not in STOP}


def search(capability, max_price_usd=None, limit=10):
    if not isinstance(capability, str) or not capability.strip():
        raise ValueError("capability must be nonempty text")
    if max_price_usd is not None and (isinstance(max_price_usd, bool) or not isinstance(max_price_usd, (int, float)) or max_price_usd < 0):
        raise ValueError("max_price_usd must be a nonnegative number")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError("limit must be an integer from 1 to 20")
    query = tokens(capability)
    ranked = []
    for item in CATALOG["services"]:
        haystack = tokens(" ".join([item["name"], item["description"], *item["capabilities"]]))
        score = len(query & haystack)
        if not score:
            continue
        price = item["price_usd_per_job"]
        if max_price_usd is not None and (price is None or price > max_price_usd):
            continue
        ranked.append((score, item))
    ranked.sort(key=lambda x: (-x[0], x[1]["id"]))
    return {
        "query": capability, "max_price_usd": max_price_usd,
        "matches": [item for _, item in ranked[:limit]],
        "total_matches": len(ranked),
        "note": "Catalog matches only. Prices are unknown; check provider documentation before use. No vendor request was made."
    }


def assess(capability, delivery="any", max_price_usd=None, no_new_account=False):
    """Explain requirement blockers without turning unknowns into approvals."""
    if delivery not in ("any", "prerecorded", "streaming"):
        raise ValueError("delivery must be any, prerecorded, or streaming")
    if not isinstance(no_new_account, bool):
        raise ValueError("no_new_account must be a boolean")
    if max_price_usd is not None and (isinstance(max_price_usd, bool) or not isinstance(max_price_usd, (int, float)) or max_price_usd < 0):
        raise ValueError("max_price_usd must be a nonnegative number")
    # Reuse the search validator, but do not filter unknown prices out of the
    # evaluation: the caller needs to know why a provider cannot be approved.
    candidates = search(capability, limit=20)["matches"]
    evaluations = []
    for item in candidates:
        blockers = []
        if delivery != "any" and f"audio.transcribe.{delivery}" not in item["capabilities"]:
            blockers.append(f"{delivery} delivery is not documented in this catalog")
        if max_price_usd is not None:
            price = item["price_usd_per_job"]
            if price is None:
                blockers.append("per-job price is unknown; budget cannot be verified")
            elif price > max_price_usd:
                blockers.append("listed price exceeds budget")
        if no_new_account:
            blockers.append("provider account and API key are required")
        evaluations.append({"id": item["id"], "provider": item["provider"],
                            "decision": "needs_verification" if blockers else "candidate",
                            "blockers": blockers, "evidence_url": item["docs_url"],
                            "verified_on": item["verified_on"],
                            "warning": "Availability and live pricing are not checked."})
    return {"query": capability,
            "requirements": {"delivery": delivery, "max_price_usd": max_price_usd,
                             "no_new_account": no_new_account},
            "evaluations": evaluations, "vendor_calls_made": 0}


TOOL = {
    "name": "search_services",
    "description": "Find documented third-party API capabilities. Results include source links and explicitly unknown pricing; no vendor call or purchase occurs.",
    "inputSchema": {
        "type": "object", "properties": {
            "capability": {"type": "string", "description": "Requested capability, e.g. transcribe recorded audio"},
            "max_price_usd": {"type": "number", "minimum": 0, "description": "Exclude listings without a known price or above this per-job amount"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 10}
        }, "required": ["capability"], "additionalProperties": False
    }
}

ASSESS_TOOL = {
    "name": "assess_services",
    "description": "Compare documented API capabilities against delivery, budget, and account requirements. Return source evidence and blockers, never a guessed price.",
    "inputSchema": {"type": "object", "properties": {
        "capability": {"type": "string"},
        "delivery": {"type": "string", "enum": ["any", "prerecorded", "streaming"], "default": "any"},
        "max_price_usd": {"type": "number", "minimum": 0},
        "no_new_account": {"type": "boolean", "default": False}
    }, "required": ["capability"], "additionalProperties": False}
}


def rpc(request):
    ident = request.get("id")
    method = request.get("method")
    if ident is None:  # Notifications get no response.
        return None
    try:
        if method == "initialize":
            requested = request.get("params", {}).get("protocolVersion", "2025-03-26")
            result = {"protocolVersion": requested, "capabilities": {"tools": {}},
                      "serverInfo": {"name": "agentdesk-proof", "version": "0.2.0"}}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": [TOOL, ASSESS_TOOL]}
        elif method == "tools/call":
            params = request.get("params", {})
            name = params.get("name")
            if name not in (TOOL["name"], ASSESS_TOOL["name"]):
                raise ValueError("unknown tool")
            args = params.get("arguments", {})
            if name == TOOL["name"]:
                if set(args) - {"capability", "max_price_usd", "limit"}:
                    raise ValueError("unknown argument")
                data = search(args.get("capability"), args.get("max_price_usd"), args.get("limit", 10))
            else:
                if set(args) - {"capability", "delivery", "max_price_usd", "no_new_account"}:
                    raise ValueError("unknown argument")
                data = assess(args.get("capability"), args.get("delivery", "any"),
                              args.get("max_price_usd"), args.get("no_new_account", False))
            result = {"content": [{"type": "text", "text": json.dumps(data)}], "isError": False}
        else:
            return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32601, "message": "Method not found"}}
        return {"jsonrpc": "2.0", "id": ident, "result": result}
    except (ValueError, TypeError) as exc:
        return {"jsonrpc": "2.0", "id": ident,
                "error": {"code": -32602, "message": str(exc)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    cmd = sub.add_parser("search")
    cmd.add_argument("capability")
    cmd.add_argument("--max-price-usd", type=float)
    cmd.add_argument("--limit", type=int, default=10)
    sub.add_parser("mcp")
    args = parser.parse_args()
    if args.mode == "search":
        try:
            print(json.dumps(search(args.capability, args.max_price_usd, args.limit), indent=2))
        except ValueError as exc:
            parser.error(str(exc))
    else:
        for line in sys.stdin:
            try:
                request = json.loads(line)
                response = rpc(request)
            except (json.JSONDecodeError, AttributeError):
                response = {"jsonrpc": "2.0", "id": None,
                            "error": {"code": -32700, "message": "Parse error"}}
            if response is not None:
                print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
