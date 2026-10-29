"""WS2 routeSubmission endpoint (contract v0.2 draft).

Request format follows Docs/Server_API_Documentation.md:
  {"MESSAGE": {"METHOD": "POST", "INFO": "routeSubmission", "PARAMS": {...}}}
Takes the PARAMS fields from the router contract, runs the tested router,
and returns a reply in the same message format the server already uses.
No database or keys in here: the server saves the result (see to_record).
"""
from router import route_decision

NEXT_PATH = {"PASS": "A", "FAIL": "B", "MANUAL_REVIEW": "instructor", "REJECTED": "none"}
REASONS = {
    None: "all mandatory checks met",
    "INVALID_UPLOAD": "upload rejected, does not count as an attempt",
    "SYNTAX_ERROR": "code did not compile or run",
    "TIMEOUT": "code ran too long",
    "MEMORY_LIMIT": "code used too much memory",
    "RUNTIME_EXCEPTION": "code crashed while running",
    "WRONG_OUTPUT": "fewer tests passed than the threshold",
    "EVALUATOR_ERROR": "our evaluator had a problem, needs a person to check",
    "TEST_SUITE_MISSING": "no test suite found, needs a person to check",
    "PROHIBITED_ACTION": "code tried something not allowed, needs a person to check",
}
REQUIRED = ["submissionID", "uploadValid", "compileStatus", "testsPassed",
            "testsTotal", "threshold"]


def _bool(v):
    return v if isinstance(v, bool) else str(v).strip().lower() == "true"


def _error(msg, original):
    return {"Response Code": "400", "MESSAGE": {"ERROR": msg, "original Message": original}}


def handle_route_submission(data):
    """data is the whole message: {"Response Code":..., "MESSAGE": {...}}"""
    try:
        m = data["MESSAGE"]["PARAMS"]
        if not isinstance(m, dict):
            raise TypeError
    except (KeyError, TypeError):
        return _error("Invalid routeSubmission request", data)
    missing = [k for k in REQUIRED if k not in m]
    if missing:
        return _error("Missing fields: " + ", ".join(missing), data)
    try:
        route, code, warnings = route_decision(
            upload_valid=_bool(m["uploadValid"]),
            compile_status=m["compileStatus"],
            error_status=m.get("errorStatus") or None,
            tests_passed=int(m["testsPassed"]),
            tests_total=int(m["testsTotal"]),
            threshold=int(m["threshold"]),
            test_suite_ok=_bool(m.get("testSuiteOk", True)),
            comment_lines=int(m.get("commentLines", 0)),
            min_comments=int(m.get("minComments", 0)),
        )
    except (ValueError, TypeError):
        return _error("Invalid routeSubmission request", data)
    return {"Response Code": "200", "MESSAGE": {
        "METHOD": "POST", "INFO": "routeSubmission",
        "submissionID": str(m["submissionID"]),
        "route": route,
        "reasonCode": code,
        "reason": REASONS[code],
        "warnings": warnings,
        "countsAsAttempt": "false" if route == "REJECTED" else "true",
        "nextPath": NEXT_PATH[route],
    }}


def to_record(reply, evaluator_version="v0.2"):
    """Flat row for the evaluation/routing table (the server saves this)."""
    m = reply["MESSAGE"]
    return {"submission_id": m["submissionID"], "route": m["route"],
            "reason_code": m["reasonCode"], "evaluator_version": evaluator_version}
