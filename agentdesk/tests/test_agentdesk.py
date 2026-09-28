import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agentdesk import search, assess


class AgentDeskTest(unittest.TestCase):
    def test_search_and_price_boundary(self):
        result = search("transcribe recorded audio")
        self.assertGreaterEqual(result["total_matches"], 2)
        self.assertEqual(search("transcribe recorded audio", max_price_usd=1)["matches"], [])
        self.assertTrue(all(item["docs_url"].startswith("https://") for item in result["matches"]))

    def test_assess_explains_blockers(self):
        result = assess("transcribe recorded audio", delivery="prerecorded",
                        max_price_usd=1, no_new_account=True)
        self.assertTrue(result["evaluations"])
        self.assertTrue(all(x["decision"] == "needs_verification" for x in result["evaluations"]))
        self.assertTrue(any("price is unknown" in b for x in result["evaluations"] for b in x["blockers"]))
        self.assertEqual(result["vendor_calls_made"], 0)

    def test_separate_client_process(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "independent-test", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search_services", "arguments": {"capability": "speech to text"}}}
        ]
        proc = subprocess.run([sys.executable, str(ROOT / "agentdesk.py"), "mcp"],
                              input="\n".join(json.dumps(x) for x in requests) + "\n",
                              text=True, capture_output=True, timeout=5, check=True)
        replies = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual([r["id"] for r in replies], [1, 2, 3])
        self.assertEqual(replies[1]["result"]["tools"][0]["name"], "search_services")
        data = json.loads(replies[2]["result"]["content"][0]["text"])
        self.assertGreater(data["total_matches"], 0)


if __name__ == "__main__":
    unittest.main()
