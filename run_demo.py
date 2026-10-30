"""Runs the 5 live-demo prompts from the test, printing answer, tool chain and latency."""
import sys, json
from app import obs; obs.QUIET = "--trace" not in sys.argv
from app.orchestrator import ChatRequest, handle
from app.data import PRODUCTS
from app.tools import compliance_filter
blocked_ca = next(p for p in PRODUCTS if compliance_filter("CA", [p["product_id"]])["results"][0]["decision"] == "blocked")
sku = blocked_ca["sku"]
SCRIPT = [("internal_sales", "Give me hot picks for CA under $5000"),
          ("internal_sales", f"Why is {sku} not available in CA? Suggest alternatives."),
          ("internal_sales", f"How much stock does {sku} have and where?"),
          ("portal_vendor", "I'm uploading a product missing Net Wt and no lab report-what do I fix?"),
          ("internal_sales", "Ok add 2 of the first one to the basket")]
sid = "demo"
for i, (ut, q) in enumerate(SCRIPT, 1):
    if i == 5: handle(ChatRequest(message="Give me hot picks for CA under $5000", user_type=ut, session_id="demo"))  # re-seed so 'first one' = a hot pick
    out = handle(ChatRequest(message=q, user_type=ut, session_id=sid if ut == "internal_sales" else "vendor-demo"))
    print(f"\n[{i}] ({ut}) {q}\n    intent={out['intent']} tools={out['tools_called']} latency={out['latency_ms']}ms\n" + "\n".join("    " + l for l in out["answer"].splitlines()))
print("\nLogs: logs/requests.jsonl (traces), logs/audit.jsonl (tool-call audit with output hashes)")
