# AgentDesk proof 0.2

A $0 experiment in agent-facing service discovery. This is a local MCP server using only Python's standard library. It searches three documented speech-to-text APIs and returns structured matches with source links. It does not call vendors, take payment, verify live prices, or claim automatic public discovery.

## Run

Python 3.10+ is sufficient. No account, API key, package install, or network access is needed for the local search.

```bash
python3 agentdesk.py search "transcribe recorded audio"
python3 agentdesk.py search "speech to text" --max-price-usd 1
python3 agentdesk.py mcp
```

The `--max-price-usd` example returns no matches because current per-job pricing cannot be established from the catalog. Unknown prices are never treated as free or under budget.

For an MCP client, configure a **local stdio server** with command `python3`, args `["/absolute/path/to/agentdesk.py", "mcp"]`. It exposes `search_services` and `assess_services`. The latter explains blockers for delivery mode, budget, and new-account requirements. An agent must be deliberately given this server configuration; the MCP server is not publicly listed.

## What the result means

Each listing gives the provider's documented capability, documentation URL, authentication requirement, last review date, and a `pricing_status` of `unknown`. A match means the catalog points to an apparently suitable API. It does **not** mean the provider is cheaper, available to the caller, approved for a particular job, or currently healthy. A `max_price_usd` filter excludes every unknown-priced listing.

## Proof gates

1. **Local protocol:** a separate MCP client process can discover and call `search_services`. Covered by `python3 -m unittest discover -s tests -v`.
2. **Outside agent:** give another agent the server configuration, but do not tell it provider names. Ask it to find a transcription API and cite the original provider documentation. Record whether it uses AgentDesk and whether the result saves time. **Not yet tested.**
3. **Public discovery and usage:** requires a reachable endpoint or package plus actual registration/distribution. **Not built.**
4. **Revenue:** requires an independently valuable service, a permitted payment route, customers, and accounting. **Not built.**

Next decision after gate 2: compare AgentDesk against a general web search on the same request. If it adds no value, change the narrow use case before publishing or spending money.

Sources in `catalog.json` were reviewed on 2026-09-28. Recheck them before making provider or pricing decisions.
