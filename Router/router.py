"""WS2 router v0.2: deterministic PASS / FAIL / MANUAL_REVIEW decision.
The AI never decides correctness. Returns (route, diagnostic_code, warning_codes)."""

def route_decision(upload_valid, compile_status, error_status, tests_passed, tests_total,
                   threshold, test_suite_ok=True, comment_lines=0, min_comments=0):
    warnings = []
    # 1. rejected before evaluation
    if not upload_valid:
        return "REJECTED", "INVALID_UPLOAD", warnings
    # 2. evaluator cannot be trusted -> MANUAL_REVIEW
    if error_status in ("CRASH", "SANDBOX_ERROR"):
        return "MANUAL_REVIEW", "EVALUATOR_ERROR", warnings
    if error_status == "PROHIBITED_ACTION":
        return "MANUAL_REVIEW", "PROHIBITED_ACTION", warnings
    if not test_suite_ok or tests_total in (0, None):
        return "MANUAL_REVIEW", "TEST_SUITE_MISSING", warnings
    # 3. student code problems -> FAIL
    if compile_status != "SUCCESS":
        return "FAIL", "SYNTAX_ERROR", warnings
    if error_status == "TIMEOUT":
        return "FAIL", "TIMEOUT", warnings
    if error_status == "MEMORY_LIMIT":
        return "FAIL", "MEMORY_LIMIT", warnings
    if error_status == "RUNTIME_EXCEPTION":
        return "FAIL", "RUNTIME_EXCEPTION", warnings
    if tests_passed < threshold:
        return "FAIL", "WRONG_OUTPUT", warnings
    # 4. PASS (minor issues never block Path A)
    if comment_lines < min_comments:
        warnings.append("MISSING_COMMENTS")
    return "PASS", None, warnings
