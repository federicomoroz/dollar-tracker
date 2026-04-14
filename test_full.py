"""
Comprehensive end-to-end test for Dollar Tracker.
Covers all endpoints, edge cases, and UI-layer validation.
Run: py test_full.py
"""

import json
import sys
import textwrap
import httpx

BASE = "http://localhost:8000"
EMAIL = "fedegfs@gmail.com"
client = httpx.Client(base_url=BASE, timeout=15)

passed = failed = 0
_created_alert_ids  = []
_created_report_ids = []


# -- helpers -------------------------------------------------------------------

def check(name, res, expect_status, validators=None):
    global passed, failed
    errors = []
    if res.status_code != expect_status:
        errors.append(f"status {res.status_code} (expected {expect_status})")
    body = None
    try:
        body = res.json()
    except Exception:
        body = res.text

    for fn in (validators or []):
        err = fn(body)
        if err:
            errors.append(err)

    if errors:
        print(f"  FAIL  {name}")
        for e in errors:
            print(f"        -> {e}")
        if body is not None:
            snippet = json.dumps(body)[:300] if not isinstance(body, str) else body[:300]
            print(f"        body: {snippet}")
        failed += 1
    else:
        print(f"  PASS  {name}")
        passed += 1

    return body


def has_key(key):
    return lambda b: None if isinstance(b, dict) and key in b else f"missing key '{key}'"

def is_list():
    return lambda b: None if isinstance(b, list) else "expected a list"

def list_len(n, op=">="):
    def v(b):
        if not isinstance(b, list):
            return "not a list"
        ok = (len(b) >= n if op == ">=" else
              len(b) == n if op == "==" else
              len(b) <= n if op == "<=" else True)
        return None if ok else f"list length {len(b)} (expected {op} {n})"
    return v

def field_equals(key, val):
    return lambda b: None if isinstance(b, dict) and b.get(key) == val else f"expected {key}={val!r}, got {b.get(key)!r}"

def field_in(key, *vals):
    return lambda b: None if isinstance(b, dict) and b.get(key) in vals else f"expected {key} in {vals}, got {b.get(key)!r}"

def contains_text(text):
    return lambda b: None if text.lower() in (b if isinstance(b, str) else "").lower() else f"expected text '{text}' not found"


# ==============================================================================
print("\n-- 1. LANDING PAGE (UI) -------------------------------------------------")

res = client.get("/")
check("GET / returns 200", res, 200)
check("Landing has rates table",       res, 200, [contains_text("COTIZACIONES ACTUALES")])
check("Landing has alerts section",    res, 200, [contains_text("ALERTAS DE PRECIO")])
check("Landing has reports section",   res, 200, [contains_text("REPORTES PERIODICOS")])
check("Landing has fetch button",      res, 200, [contains_text("FETCH AHORA")])
check("Landing has API docs link",     res, 200, [contains_text('href="/docs"')])
check("Landing has rate options",      res, 200, [contains_text('value="blue"')])
check("Landing has report frequency",  res, 200, [contains_text('value="daily"')])
check("Landing shows last updated",    res, 200, [contains_text("Ultima actualizacion")])
check("Landing has delete JS",         res, 200, [contains_text("deleteAlert")])
check("Landing has loadReports JS",    res, 200, [contains_text("loadReports")])
check("No raw Python placeholders",    res, 200, [lambda b: None if "{{" not in b else "unresolved placeholder found"])


# ==============================================================================
print("\n-- 2. RATES -- CURRENT ---------------------------------------------------")

body = check("GET /rates/current returns list", client.get("/rates/current"), 200, [is_list(), list_len(1)])
if isinstance(body, list) and body:
    r = body[0]
    check("Rate has required fields", client.get("/rates/current"), 200,
          [lambda b: None if all(k in b[0] for k in ("id","type","name","sell","fetched_at")) else "missing fields"])
    check("Rate sell is numeric",  client.get("/rates/current"), 200,
          [lambda b: None if isinstance(b[0]["sell"], (int, float)) else "sell not numeric"])
    check("Rate fetched_at is str", client.get("/rates/current"), 200,
          [lambda b: None if isinstance(b[0]["fetched_at"], str) else "fetched_at not str"])


# ==============================================================================
print("\n-- 3. RATES -- HISTORY ---------------------------------------------------")

check("GET /rates/history default",          client.get("/rates/history"),                    200, [is_list()])
check("GET /rates/history ?days=7",          client.get("/rates/history?days=7"),             200, [is_list()])
check("GET /rates/history ?type=blue",       client.get("/rates/history?type=blue"),          200, [is_list()])
check("GET /rates/history ?type=blue&days=7", client.get("/rates/history?type=blue&days=7"), 200, [is_list()])
check("GET /rates/history ?limit=5",         client.get("/rates/history?limit=5"),            200, [is_list(), list_len(0, ">="), list_len(5, "<=")])
check("GET /rates/history days=0 -> 422",     client.get("/rates/history?days=0"),             422)
check("GET /rates/history days=91 -> 422",    client.get("/rates/history?days=91"),            422)
check("GET /rates/history limit=0 -> 422",    client.get("/rates/history?limit=0"),            422)
check("GET /rates/history limit=1001 -> 422", client.get("/rates/history?limit=1001"),         422)
check("GET /rates/history unknown type",     client.get("/rates/history?type=nonexistent"),   200, [is_list(), list_len(0, "==")])


# ==============================================================================
print("\n-- 4. RATES -- STATS -----------------------------------------------------")

check("GET /rates/stats ?type=blue",          client.get("/rates/stats?type=blue"),           200,
      [has_key("min_sell"), has_key("max_sell"), has_key("avg_sell"), has_key("samples")])
check("GET /rates/stats ?type=blue&days=7",   client.get("/rates/stats?type=blue&days=7"),    200)
check("GET /rates/stats missing type -> 422",  client.get("/rates/stats"),                     422)
check("GET /rates/stats unknown type",        client.get("/rates/stats?type=nonexistent"),    200,
      [lambda b: None if b.get("samples") == 0 else f"expected 0 samples, got {b.get('samples')}"])
check("GET /rates/stats days=0 -> 422",        client.get("/rates/stats?type=blue&days=0"),    422)
check("GET /rates/stats days=91 -> 422",       client.get("/rates/stats?type=blue&days=91"),   422)


# ==============================================================================
print("\n-- 5. RATES -- MANUAL FETCH ----------------------------------------------")

body = check("POST /rates/fetch returns list", client.post("/rates/fetch"), 200, [is_list(), list_len(1)])
check("GET on /rates/fetch -> 405",            client.get("/rates/fetch"),  405)


# ==============================================================================
print("\n-- 6. ALERTS -- CREATE (valid) -------------------------------------------")

def make_alert(payload):
    return client.post("/alerts", json=payload)

r = make_alert({"email": EMAIL, "rate_type": "blue",    "max_threshold": 1300.0})
b = check("Alert: max only",            r, 201, [has_key("id"), field_equals("active", True)])
if isinstance(b, dict): _created_alert_ids.append(b["id"])

r = make_alert({"email": EMAIL, "rate_type": "oficial", "min_threshold": 800.0})
b = check("Alert: min only",            r, 201, [has_key("id")])
if isinstance(b, dict): _created_alert_ids.append(b["id"])

r = make_alert({"email": EMAIL, "rate_type": "blue",    "min_threshold": 700.0, "max_threshold": 1500.0})
b = check("Alert: both min + max",      r, 201, [has_key("id")])
if isinstance(b, dict): _created_alert_ids.append(b["id"])

r = make_alert({"email": EMAIL, "rate_type": "cripto",  "max_threshold": 0.01})
b = check("Alert: near-zero threshold", r, 201, [has_key("id")])
if isinstance(b, dict): _created_alert_ids.append(b["id"])

r = make_alert({"email": EMAIL, "rate_type": "tarjeta", "min_threshold": 1.0, "max_threshold": 99999999.0})
b = check("Alert: extreme thresholds",  r, 201, [has_key("id")])
if isinstance(b, dict): _created_alert_ids.append(b["id"])


# ==============================================================================
print("\n-- 7. ALERTS -- CREATE (invalid) -----------------------------------------")

check("Alert: no thresholds -> 422",
      make_alert({"email": EMAIL, "rate_type": "blue"}), 422)

check("Alert: null thresholds explicit -> 422",
      make_alert({"email": EMAIL, "rate_type": "blue", "min_threshold": None, "max_threshold": None}), 422)

check("Alert: bad email -> 422",
      make_alert({"email": "notanemail", "rate_type": "blue", "max_threshold": 1000}), 422)

check("Alert: missing email -> 422",
      make_alert({"rate_type": "blue", "max_threshold": 1000}), 422)

check("Alert: missing rate_type -> 422",
      make_alert({"email": EMAIL, "max_threshold": 1000}), 422)

check("Alert: empty body -> 422",
      client.post("/alerts", content=b""), 422)

check("Alert: malformed JSON -> 422",
      client.post("/alerts", content=b"{bad json}", headers={"Content-Type": "application/json"}), 422)


# ==============================================================================
print("\n-- 8. ALERTS -- LIST -----------------------------------------------------")

body = check("GET /alerts returns list", client.get("/alerts"), 200, [is_list(), list_len(len(_created_alert_ids))])
if isinstance(body, list) and body:
    a = body[0]
    check("Alert item has all fields", client.get("/alerts"), 200,
          [lambda b: None if all(k in b[0] for k in ("id","email","rate_type","min_threshold","max_threshold","active","last_alerted","created_at")) else "missing fields"])


# ==============================================================================
print("\n-- 9. ALERTS -- DELETE ---------------------------------------------------")

if _created_alert_ids:
    del_id = _created_alert_ids.pop()
    check(f"DELETE /alerts/{del_id} -> 204",   client.delete(f"/alerts/{del_id}"),  204)
    check(f"DELETE /alerts/{del_id} again -> 404", client.delete(f"/alerts/{del_id}"), 404)

check("DELETE /alerts/999999 -> 404",          client.delete("/alerts/999999"),      404)
check("DELETE /alerts/abc -> 422",             client.delete("/alerts/abc"),         422)


# ==============================================================================
print("\n-- 10. REPORTS -- CREATE (valid) -----------------------------------------")

def make_report(payload):
    return client.post("/reports", json=payload)

r = make_report({"email": EMAIL, "frequency": "daily"})
b = check("Report: daily",   r, 201, [has_key("id"), field_equals("active", True), field_equals("frequency", "daily")])
if isinstance(b, dict): _created_report_ids.append(b["id"])

r = make_report({"email": EMAIL, "frequency": "hourly"})
b = check("Report: hourly",  r, 201, [has_key("id")])
if isinstance(b, dict): _created_report_ids.append(b["id"])

r = make_report({"email": EMAIL, "frequency": "weekly"})
b = check("Report: weekly",  r, 201, [has_key("id")])
if isinstance(b, dict): _created_report_ids.append(b["id"])


# ==============================================================================
print("\n-- 11. REPORTS -- CREATE (invalid) ---------------------------------------")

check("Report: bad frequency -> 422",
      make_report({"email": EMAIL, "frequency": "monthly"}), 422)

check("Report: empty frequency -> 422",
      make_report({"email": EMAIL, "frequency": ""}), 422)

check("Report: bad email -> 422",
      make_report({"email": "notanemail", "frequency": "daily"}), 422)

check("Report: missing email -> 422",
      make_report({"frequency": "daily"}), 422)

check("Report: missing frequency -> 422",
      make_report({"email": EMAIL}), 422)

check("Report: empty body -> 422",
      client.post("/reports", content=b""), 422)


# ==============================================================================
print("\n-- 12. REPORTS -- LIST ---------------------------------------------------")

body = check("GET /reports returns list", client.get("/reports"), 200, [is_list(), list_len(len(_created_report_ids))])
if isinstance(body, list) and body:
    check("Report item has all fields", client.get("/reports"), 200,
          [lambda b: None if all(k in b[0] for k in ("id","email","frequency","active","last_sent","created_at")) else "missing fields"])


# ==============================================================================
print("\n-- 13. REPORTS -- DELETE -------------------------------------------------")

if _created_report_ids:
    del_id = _created_report_ids.pop()
    check(f"DELETE /reports/{del_id} -> 204",      client.delete(f"/reports/{del_id}"), 204)
    check(f"DELETE /reports/{del_id} again -> 404", client.delete(f"/reports/{del_id}"), 404)

check("DELETE /reports/999999 -> 404",             client.delete("/reports/999999"),     404)
check("DELETE /reports/abc -> 422",                client.delete("/reports/abc"),         422)


# ==============================================================================
print("\n-- 14. SWAGGER / DOCS ---------------------------------------------------")

check("GET /docs returns 200",    client.get("/docs"),    200)
check("GET /openapi.json -> 200",  client.get("/openapi.json"), 200, [has_key("paths")])


# ==============================================================================
print("\n-- 15. 404 / UNKNOWN ROUTES ---------------------------------------------")

check("GET /nonexistent -> 404",    client.get("/nonexistent"),  404)
check("GET /rates/unknown -> 404",  client.get("/rates/unknown"), 404)


# ==============================================================================
print("\n-- 16. STATIC ASSETS ----------------------------------------------------")

check("GET /static/favicon.svg -> 200", client.get("/static/favicon.svg"), 200)


# ==============================================================================
print("\n-- 17. CLEANUP -- delete remaining test data ------------------------------")

for aid in _created_alert_ids:
    r = client.delete(f"/alerts/{aid}")
    print(f"  {'PASS' if r.status_code == 204 else 'FAIL'}  cleanup alert {aid}: {r.status_code}")

for rid in _created_report_ids:
    r = client.delete(f"/reports/{rid}")
    print(f"  {'PASS' if r.status_code == 204 else 'FAIL'}  cleanup report {rid}: {r.status_code}")


# ==============================================================================
print(f"\n{'-'*60}")
print(f"  Results: {passed} passed, {failed} failed")
print(f"{'-'*60}\n")
sys.exit(0 if failed == 0 else 1)
