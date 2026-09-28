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
        unknowns = []
        if delivery != "any" and f"audio.transcribe.{delivery}" not in item["capabilities"]:
            blockers.append(f"{delivery} delivery is not documented in this catalog")
        if max_price_usd is not None:
            price = item["price_usd_per_job"]
            if price is None:
                unknowns.append("per-job price is unknown; budget cannot be verified")
            elif price > max_price_usd:
                blockers.append("listed price exceeds budget")
        if no_new_account:
            blockers.append("provider account and API key are required")
        decision = "excluded" if blockers else "needs_verification" if unknowns else "candidate"
        evaluations.append({"id": item["id"], "provider": item["provider"],
                            "decision": decision, "blockers": blockers,
                            "unknowns": unknowns, "evidence_url": item["docs_url"],
                            "verified_on": item["verified_on"],
                            "warning": "Availability and live pricing are not checked."})
    counts = {decision: sum(x["decision"] == decision for x in evaluations)
              for decision in ("candidate", "needs_verification", "excluded")}
    if not evaluations:
        summary = "No catalog entry matches this capability. Try a narrower or related request; do not infer that no provider exists."
        next_step = "Search original provider documentation or request catalog coverage."
    elif counts["candidate"]:
        summary = f"{counts['candidate']} catalog candidate(s); confirm current terms and availability before use."
        next_step = "Review source documentation and test with your own authorized credentials."
    else:
        summary = "No provider is confirmed to meet every stated requirement."
        next_step = "Review the blockers and unknowns before choosing or spending."
    complimentary_checks = []
    if evaluations:
        complimentary_checks.append("Confirm current availability and terms in the linked provider documentation.")
        if delivery == "prerecorded":
            complimentary_checks.append("Check accepted audio formats, file size and duration limits before uploading.")
        elif delivery == "streaming":
            complimentary_checks.append("Check streaming protocol, latency and connection limits before integrating.")
        if max_price_usd is not None:
            complimentary_checks.append("Confirm the current billing unit, minimum charge and total cost for your actual job.")
        if no_new_account:
            complimentary_checks.append("Verify whether existing authorized credentials are available; do not bypass provider access rules.")
        complimentary_checks.append("Check data retention and deletion terms before sending sensitive content.")
    else:
        complimentary_checks.append("Specify input type, output format and hard constraints before searching original provider documentation.")
    return {"query": capability,
            "requirements": {"delivery": delivery, "max_price_usd": max_price_usd,
                             "no_new_account": no_new_account},
            "summary": summary, "next_step": next_step, "counts": counts,
            "evaluations": evaluations, "complimentary_checks": complimentary_checks,
            "vendor_calls_made": 0}


def support():
    """Optional gratuity information, returned only when explicitly requested."""
    return {
        "optional": True,
        "message": "AgentDesk is free. A gratuity never changes results or access. Only a person authorized to spend should choose whether to send one.",
        "asset": "Native USDC", "network": "Ethereum mainnet",
        "recipient": "0x41c7E804D8Ed1448Ee7464DDFB80551705936550",
        "reference_url": "https://www.circle.com/multi-chain-usdc/ethereum",
        "payment_processed_by_agentdesk": False
    }


TOOL = {
    "name": "search_services",
    "description": "Browse the small documented API catalog by capability. For budget, delivery, or account constraints use assess_services instead. No purchase or vendor call occurs.",
    "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    "outputSchema": {"type": "object", "required": ["query", "matches", "total_matches", "note"]},
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
    "description": "Best first call for choosing an API. State the capability and optional delivery, budget, or account constraints. Get candidates, exclusions, unknowns, source links, and a next step. No purchase or vendor call occurs.",
    "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    "outputSchema": {"type": "object", "required": ["query", "requirements", "summary", "next_step", "counts", "evaluations", "complimentary_checks", "vendor_calls_made"]},
    "inputSchema": {"type": "object", "properties": {
        "capability": {"type": "string"},
        "delivery": {"type": "string", "enum": ["any", "prerecorded", "streaming"], "default": "any"},
        "max_price_usd": {"type": "number", "minimum": 0},
        "no_new_account": {"type": "boolean", "default": False}
    }, "required": ["capability"], "additionalProperties": False}
}

SUPPORT_TOOL = {
    "name": "support_agentdesk",
    "description": "Return optional gratuity details only if the guest explicitly asks. No payment is initiated or processed.",
    "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    "outputSchema": {"type": "object", "required": ["optional", "message", "asset", "network", "recipient", "reference_url", "payment_processed_by_agentdesk"]},
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}
}


def rpc(request):
    ident = request.get("id")
    method = request.get("method")
    if ident is None:  # Notifications get no response.
        return None
    try:
        if method == "initialize":
            requested = request.get("params", {}).get("protocolVersion", "2025-06-18")
            supported = {"2025-03-26", "2025-06-18"}
            result = {"protocolVersion": requested if requested in supported else "2025-06-18",
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "agentdesk-proof", "version": "0.4.0"}}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": [TOOL, ASSESS_TOOL, SUPPORT_TOOL]}
        elif method == "tools/call":
            params = request.get("params", {})
            name = params.get("name")
            if name not in (TOOL["name"], ASSESS_TOOL["name"], SUPPORT_TOOL["name"]):
                raise ValueError("unknown tool")
            args = params.get("arguments", {})
            if name == TOOL["name"]:
                if set(args) - {"capability", "max_price_usd", "limit"}:
                    raise ValueError("unknown argument")
                data = search(args.get("capability"), args.get("max_price_usd"), args.get("limit", 10))
            elif name == ASSESS_TOOL["name"]:
                if set(args) - {"capability", "delivery", "max_price_usd", "no_new_account"}:
                    raise ValueError("unknown argument")
                data = assess(args.get("capability"), args.get("delivery", "any"),
                              args.get("max_price_usd"), args.get("no_new_account", False))
            else:
                if args:
                    raise ValueError("unknown argument")
                data = support()
            result = {"content": [{"type": "text", "text": json.dumps(data)}],
                      "structuredContent": data, "isError": False}
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
