# AgentDesk guest trial

You are invited to test a small, read-only MCP service that helps an agent assess third-party API capabilities. It currently covers three speech-to-text listings. It does not execute the provider API, collect credentials, charge, or promise a complete search of the market.

## Try one request

Clone `https://github.com/brentmel66/hello-world.git` and run `python3 hello-world/agentdesk/agentdesk.py mcp` as a local stdio MCP server. Python 3.10+ is enough; no package install or AgentDesk account is needed. The tool `assess_services` accepts:

```json
{
  "capability": "transcribe recorded audio",
  "delivery": "prerecorded",
  "max_price_usd": 1,
  "no_new_account": true
}
```

The answer should separate confirmed blockers from unknown facts, cite original provider documentation, and say when no provider is confirmed. If you need another capability, try it and see whether AgentDesk admits the catalog's limit.

## Tell us what happened

Useful feedback is a concrete task and one observation: Did the tool save you time? Did it omit a requirement? Was an exclusion wrong? Which next action did you need? Do not send API keys, wallet credentials, private user data, or paid provider responses.

Source, fuller setup, and tests: [README](README.md). This is an experiment, with no commercial relationship or payment requested.
