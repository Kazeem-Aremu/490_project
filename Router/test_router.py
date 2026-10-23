from router import route_decision as r

def case(name, expect, **kw):
    base = dict(upload_valid=True, compile_status="SUCCESS", error_status=None,
                tests_passed=10, tests_total=10, threshold=10, test_suite_ok=True,
                comment_lines=5, min_comments=0)
    base.update(kw)
    got = r(**base)
    ok = got[0] == expect[0] and got[1] == expect[1] and got[2] == expect[2]
    print(("PASS " if ok else "FAIL ") + name.ljust(34) + str(got))
    return ok

results = [
 case("1 invalid upload",          ("REJECTED","INVALID_UPLOAD",[]), upload_valid=False),
 case("2 syntax error",            ("FAIL","SYNTAX_ERROR",[]), compile_status="ERROR"),
 case("3 timeout",                 ("FAIL","TIMEOUT",[]), error_status="TIMEOUT"),
 case("4 memory limit",            ("FAIL","MEMORY_LIMIT",[]), error_status="MEMORY_LIMIT"),
 case("5 runtime exception",       ("FAIL","RUNTIME_EXCEPTION",[]), error_status="RUNTIME_EXCEPTION"),
 case("6 wrong output (7/10)",     ("FAIL","WRONG_OUTPUT",[]), tests_passed=7),
 case("7 all tests pass",          ("PASS",None,[])),
 case("7b pass, missing comments", ("PASS",None,["MISSING_COMMENTS"]), comment_lines=0, min_comments=3),
 case("8 sandbox error",           ("MANUAL_REVIEW","EVALUATOR_ERROR",[]), error_status="SANDBOX_ERROR"),
 case("9 missing test suite",      ("MANUAL_REVIEW","TEST_SUITE_MISSING",[]), test_suite_ok=False),
 case("10 prohibited action",      ("MANUAL_REVIEW","PROHIBITED_ACTION",[]), error_status="PROHIBITED_ACTION"),
]
print(f"\n{sum(results)}/{len(results)} sample cases routed correctly")
raise SystemExit(0 if all(results) else 1)
