"""End-to-end smoke test against a running backend.

Usage:  .venv/Scripts/python.exe scripts/smoke_v2.py [base_url]
Walks one circular through: analyse -> Gate 1 -> Gate 2 -> evidence -> compliant,
then verifies the audit hash chain.
"""
import sys
import time

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000") + "/api/v2"
c = httpx.Client(timeout=60)


def ok(r):
    if r.status_code >= 400:
        raise SystemExit(f"{r.request.method} {r.request.url} -> {r.status_code}: {r.text}")
    return r.json()


circs = ok(c.get(f"{BASE}/circulars"))
print(f"{len(circs)} circulars")
target = next((x for x in circs if "103314" in x["reference"]), circs[0])
if target["status"] in ("created", "failed", "changes_requested"):
    ok(c.post(f"{BASE}/circulars/{target['id']}/analyze"))
wf_id = target["workflow_id"]
for _ in range(60):
    wf = ok(c.get(f"{BASE}/workflows/{wf_id}"))
    if wf["status"] not in ("created", "in_analysis"):
        break
    time.sleep(0.5)
print("after analysis:", wf["status"], "-", wf["analysis"]["summary"] if wf.get("analysis") else "")
for o in wf["obligations"]:
    print(f"   {o['code']} [{o['risk']}] {'APPL' if o['applicable'] else 'n/a '} {o['clause_ref']}: {o['title']}")
if wf["status"] == "pending_approval_1":
    ok(c.post(f"{BASE}/workflows/{wf_id}/gate/gate_1", json={"decision": "approved", "comment": "Interpretation OK"}))
wf = ok(c.get(f"{BASE}/workflows/{wf_id}"))
print("after gate 1:", wf["status"], "| tasks in plan:", len((wf.get("plan") or {}).get("tasks", [])))
if wf["status"] == "pending_approval_2":
    ok(c.post(f"{BASE}/workflows/{wf_id}/gate/gate_2", json={"decision": "approved", "comment": "Plan OK"}))
wf = ok(c.get(f"{BASE}/workflows/{wf_id}"))
print("after gate 2:", wf["status"], "| tasks:", len(wf["tasks"]))
for t in wf["tasks"]:
    if t["raw_status"] == "Completed":
        continue
    if t["evidence_requirement"]:
        ok(c.post(f"{BASE}/tasks/{t['id']}/evidence", data={"note": "Done", "complete": "true"},
                  files={"file": ("evidence.txt", b"proof for " + t["title"].encode(), "text/plain")}))
    else:
        ok(c.patch(f"{BASE}/tasks/{t['id']}", json={"status": "Completed", "note": "Done"}))
wf = ok(c.get(f"{BASE}/workflows/{wf_id}"))
print("final:", wf["status"], wf["progress"])
dash = ok(c.get(f"{BASE}/dashboard"))
print("dashboard health:", dash["health"], "pipeline:", dash["pipeline"])
print("audit chain:", ok(c.get(f"{BASE}/audit/verify")))
