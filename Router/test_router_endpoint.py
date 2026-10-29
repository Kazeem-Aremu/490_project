from router_endpoint import handle_route_submission as h

def msg(**kw):
    base = {"submissionID": "8765", "uploadValid": "true", "compileStatus": "SUCCESS",
            "errorStatus": "", "testsPassed": "5", "testsTotal": "5", "threshold": "5"}
    base.update(kw)
    return {"MESSAGE": {"METHOD": "POST", "INFO": "routeSubmission", "PARAMS": base}}

def check(name, reply, route=None, path=None, attempt=None, code=None):
    m = reply["MESSAGE"]
    if code:
        ok = reply["Response Code"] == code
    else:
        ok = (reply["Response Code"] == "200" and m["route"] == route
              and m["nextPath"] == path and m["countsAsAttempt"] == attempt)
    print(("PASS " if ok else "FAIL ") + name)
    return ok

r = [
 check("all tests pass -> PASS, Path A", h(msg()), "PASS", "A", "true"),
 check("7 of 10 -> FAIL, Path B", h(msg(testsPassed="7", testsTotal="10", threshold="10")), "FAIL", "B", "true"),
 check("timeout -> FAIL, Path B", h(msg(errorStatus="TIMEOUT")), "FAIL", "B", "true"),
 check("bad upload -> REJECTED, no attempt", h(msg(uploadValid="false")), "REJECTED", "none", "false"),
 check("evaluator crash -> MANUAL_REVIEW", h(msg(errorStatus="CRASH")), "MANUAL_REVIEW", "instructor", "true"),
 check("zero tests -> MANUAL_REVIEW", h(msg(testsTotal="0", testsPassed="0")), "MANUAL_REVIEW", "instructor", "true"),
 check("missing field -> 400", h({"MESSAGE": {"METHOD": "POST", "INFO": "routeSubmission", "PARAMS": {"submissionID": "1"}}}), code="400"),
 check("bad number -> 400", h(msg(testsPassed="five")), code="400"),
 check("not a message -> 400", h("hello"), code="400"),
]
print(f"\n{sum(r)}/{len(r)} endpoint tests passed")
raise SystemExit(0 if all(r) else 1)
