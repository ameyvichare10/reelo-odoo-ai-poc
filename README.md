# Odoo + AI/LLM Orchestrator - Tool-first PoC

**Run (one command):** `./run.sh` (installs deps, runs 12 tests, runs the 5 live-demo prompts) - `./run.sh serve` starts the API.
```
curl -X POST localhost:8000/chat -H 'content-type: application/json' \
 -d '{"message":"Give me hot picks for CA under $5000","user_type":"internal_sales","session_id":"s1"}'
```
`data/seed_data.json` is synthetic (same schema as the test). To use the official file just overwrite it. Compliance rules are synthetic (`data/compliance_rules.json`, versioned) - not legal advice. LLM is **optional** (`OPENAI_API_KEY`); it only rephrases tool results and is gated by a validator.

## Architecture (1 page)
```
request{user_type, session_id, message}
  -> router.py      regex/keyword intent scoring + entity extraction + follow-up resolution (0 LLM calls)
  -> chains.py      planner: canonical tool chain per intent; whole chain authorized BEFORE any tool runs
  -> runner.py      ToolRunner: allowlist (policy.py) -> Pydantic validation -> timing -> audit (obs.py)
  -> tools.py       5 required deterministic tools (+ add_to_basket) over seed data
  -> compose.py     deterministic template -> optional llm.py polish -> validate() (no invented SKUs/numbers, no blocked recs)
  -> orchestrator   updates state.py (last_intent/state/budget/product_ids), writes trace
```
**Truth vs Knowledge lanes:** SALES/COMPLIANCE/OPS/VENDOR are *Truth* lanes - answers are built only from tool output. GENERAL_KB is the *Knowledge* lane (keyword search; embeddings could be added here, never for stock/legality).

| Concern | Where |
|---|---|
| Routing | `app/router.py` (`route`, `extract_vendor_attributes`) |
| Chains A/B/C + ops/KB/basket | `app/chains.py` |
| Tools + schemas | `app/tools.py` |
| Compliance gate (blocked > review > allowed, fails closed) | `tools.compliance_filter` + `data/compliance_rules.json` |
| Allowlists / permissions | `app/policy.py`, enforced in `app/runner.py` |
| State (memory) | `app/state.py` (dict; Redis in prod) |
| Observability | `app/obs.py` -> `logs/requests.jsonl` (trace) + `logs/audit.jsonl` (per tool call, args + output SHA-256) |
| PII redaction | `app/redact.py` - applied to LLM input (`llm.py`, `chains.kb`) and to all logs |

**Token/latency:** router is regex (sub-ms); tools return top-N rows only (hot_picks over-fetches 25 then compliance filters); the LLM (if on) sees <= ~3.5k chars of facts, never the dataset. Typical request: 1-3 ms without LLM.

**Design choices / assumptions**
- *Budget*: treated as a cap on an order of one unit of each recommended pick (greedy by rank), plus a per-unit price filter. Documented in `chains.fit_budget`.
- Follow-up ("add 2 of the first one") keeps intent = previous intent, `action=ADD_TO_BASKET`; it re-runs `compliance_filter` before `add_to_basket`, which also checks stock.
- `portal_customer` with `customer_id` has destination state **locked to the profile** (cannot be spoofed in text).
- `kb_search` visibility (public/vendor/internal) is enforced inside the tool using the trusted `user_type`.
- `vendor_validate`: explicitly blank fields = *missing*; never-supplied fields = *not provided* (REVIEW); missing field or required doc = FAIL.
- Tool failure -> degraded message, never a guessed answer.

**Tests / evaluator:** `pytest` checks expected tool-chain vs observed per intent, blocked-never-recommended across all 51 states, allowlists, memory, KB visibility, fail-closed state, PII redaction.

See `docs/LEADERSHIP_AND_SCALE.md` for team breakdown (A3) and scale/reliability (A4), and `docs/architecture.png`.
