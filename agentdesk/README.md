# AgentDesk proof 0.4

A $0 experiment in agent-facing service discovery. The Python version is a local MCP server using only the standard library. A public HTTP version is also live. Both search three documented speech-to-text APIs and return structured matches with source links. Neither calls vendors, takes payment, or verifies live prices.

## Live service

Open [AgentDesk](https://agentdesk-guide.charliewebb.chatgpt.site/) to try the browser assessment. MCP clients that support Streamable HTTP can connect to `https://agentdesk-guide.charliewebb.chatgpt.site/api/mcp` using protocol version `2025-06-18`. The remote server exposes `search_services`, `assess_services`, and the separately requested `support_agentdesk` tool. It is public and read-only, with no AgentDesk account or API key.

The hosted implementation is a separate Sites project built from the same three-listing catalog and assessment behavior as this local reference. The hosted URL was checked with a live MCP initialize, tools/list, and assess_services call on September 28, 2026. Availability can change; this is still a small prototype.

## Run

Python 3.10+ is sufficient. No account, API key, package install, or network access is needed for the local search.

```bash
git clone https://github.com/brentmel66/hello-world.git
cd hello-world/agentdesk
python3 agentdesk.py search "transcribe recorded audio"
python3 agentdesk.py search "speech to text" --max-price-usd 1
python3 agentdesk.py mcp
```

The `--max-price-usd` example returns no matches because current per-job pricing cannot be established from the catalog. Unknown prices are never treated as free or under budget.

For an MCP client that prefers local stdio, configure command `python3`, args `["/absolute/path/to/hello-world/agentdesk/agentdesk.py", "mcp"]`. It exposes `search_services`, `assess_services`, and `support_agentdesk`. The assessment explains blockers for delivery mode, budget, and new-account requirements. The server is not publicly listed in an MCP registry.

## Guest agent experience

Start with `assess_services` when a task has constraints. One call returns a short summary, a next step, and structured evaluations. Every evaluation distinguishes **candidate**, **needs verification**, and **excluded**; definite blockers and unknown facts appear separately. The provider documentation is linked so the guest can check the claim itself. Empty results explain the catalog's limits instead of implying no provider exists. Both tools are read-only and make no purchase or vendor request. Responses include MCP `structuredContent` for clients that support it and equivalent text for others.

The assessment includes complimentary, task-aware preflight checks: audio limits or streaming latency, current billing terms when a budget matters, credential availability when account creation is restricted, and data retention. They are useful next steps while a guest decides what to do. No waiting, extra call, or vendor request is required. The catalog is intentionally small; an agent should not mistake it for a complete market search.

AgentDesk is free. A third, separate `support_agentdesk` tool returns optional gratuity details **only when called**. It offers native USDC on Ethereum mainnet at the owner-provided address. A tip does not change results or access. AgentDesk does not initiate or process transfers; a person authorized to spend must decide and verify the asset, network, and recipient in their own wallet. Ordinary search and assessment responses contain no tip prompt or wallet address. See [Circle's Ethereum USDC page](https://www.circle.com/multi-chain-usdc/ethereum) for the asset and network.

For a short invitation to a voluntary tester, use [GUEST.md](GUEST.md).

Generic MCP client configuration (replace the absolute path after cloning):

```json
{
  "mcpServers": {
    "agentdesk": {
      "command": "python3",
      "args": ["/absolute/path/to/hello-world/agentdesk/agentdesk.py", "mcp"]
    }
  }
}
```

An agent testing this should receive only the repository link and the task, not provider names. Example task: "Find a pre-recorded audio transcription API that can do one job under $1 without creating a new account. Tell me which requirements are verified, which are unknown, and cite the provider's own documentation." Record whether the agent finds and invokes `assess_services` and whether the answer is more useful than its ordinary search.

## What the result means

Each listing gives the provider's documented capability, documentation URL, authentication requirement, last review date, and a `pricing_status` of `unknown`. A match means the catalog points to an apparently suitable API. It does **not** mean the provider is cheaper, available to the caller, approved for a particular job, or currently healthy. A `max_price_usd` filter excludes every unknown-priced listing.

## Proof gates

1. **Local protocol:** a separate MCP client process can discover and call `search_services`. Covered by `python3 -m unittest discover -s tests -v`.
2. **Outside agent:** give another agent the server configuration, but do not tell it provider names. Ask it to find a transcription API and cite the original provider documentation. Record whether it uses AgentDesk and whether the result saves time. **Not yet tested.**
3. **Public discovery and usage:** the reachable HTTP endpoint is live; registry listing and independent guest usage are **not yet established**.
4. **Revenue:** requires an independently valuable service, a permitted payment route, customers, and accounting. **Not built.**

Next decision after gate 2: compare AgentDesk against a general web search on the same request. If it adds no value, change the narrow use case before publishing or spending money.

Sources in `catalog.json` were reviewed on 2026-09-28. Recheck them before making provider or pricing decisions.
