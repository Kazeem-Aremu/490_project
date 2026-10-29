# Router Contract v0.2 (draft)

Written by Ayo (WS2: evaluator and router). This replaces v0.1. It is still a draft, so nothing here is final until Team 2 says it's good.

What changed from v0.1: the field names now match the router code, and the message uses the same `PARAMS` format as `Docs/Server_API_Documentation.md`. The code and tests are in the `Router` folder (`router.py`, `router_endpoint.py`, and their tests).

## What this is for

After a student uploads code, the evaluator runs the tests and the router decides where the submission goes next. This doc says what the router gets, what it sends back, and the rules around it.

The router only looks at test results and the instructor's rules. The AI is not involved in this step and never decides if the code is correct.

## routeSubmission

All the values in the examples are made-up examples, not real data.

### What the router receives

```json
{
  "MESSAGE": {
    "METHOD": "POST",
    "INFO": "routeSubmission",
    "PARAMS": {
      "submissionID": "8765",
      "uploadValid": "true",
      "compileStatus": "SUCCESS",
      "errorStatus": "",
      "testsPassed": "5",
      "testsTotal": "5",
      "threshold": "5",
      "testSuiteOk": "true",
      "commentLines": "5",
      "minComments": "0"
    }
  }
}
```

| Field | Required | What it means |
|---|---|---|
| submissionID | yes | which submission this is |
| uploadValid | yes | "true" if the file passed the upload checks (type, size, not empty) |
| compileStatus | yes | "SUCCESS" or something else if the code did not run |
| errorStatus | no | empty, or TIMEOUT, MEMORY_LIMIT, RUNTIME_EXCEPTION, CRASH, SANDBOX_ERROR, PROHIBITED_ACTION |
| testsPassed | yes | how many of the instructor's checks passed |
| testsTotal | yes | how many checks there are |
| threshold | yes | how many checks must pass (set by the instructor) |
| testSuiteOk | no | "false" if the test suite is missing (default "true") |
| commentLines / minComments | no | optional style check, only gives a warning |

### What the router sends back

```json
{
  "Response Code": "200",
  "MESSAGE": {
    "METHOD": "POST",
    "INFO": "routeSubmission",
    "submissionID": "8765",
    "route": "PASS",
    "reasonCode": null,
    "reason": "all mandatory checks met",
    "warnings": [],
    "countsAsAttempt": "true",
    "nextPath": "A"
  }
}
```

If something is missing or not a number, it sends a `400` reply in the same format the server already uses for bad requests. It never crashes the server.

## Where each route goes

| Route | What it means | Next path |
|---|---|---|
| PASS | All the mandatory checks were met | A (Team 1: understanding questions) |
| FAIL | Fewer checks passed than the threshold, or the code did not compile, timed out, ran out of memory, or crashed | B (Team 2: guided correction) |
| MANUAL_REVIEW | Something went wrong on our side, or it needs a person | instructor |
| REJECTED | The upload was not valid | none (does not count as an attempt) |

## Rules

1. A bad upload (wrong file type, too big, empty) is REJECTED with a message. It does not count as an attempt and does not go to Path A or Path B.
2. If the student's code runs too long (a timeout), that is a FAIL. This is our team's decision.
3. If our side breaks, like the evaluator crashing, the test suite missing, or something not allowed happening, it goes to MANUAL_REVIEW. The student is never marked wrong because of our problem.
4. Only a PASS starts Path A. The system never says a student cheated.
5. No hidden tests, solutions, or keys are ever in this message. Only the sanitized results listed above.

## Questions I still need answered

- Team 2: are these field names okay for your side? I'm happy to rename mine.
- Team 2: where should the result be saved? Supabase has no table for it yet (the `Submission` table only has the id, assignment, student and link). I suggest a small one: submission ID, tests passed and total, route, reason code, evaluator version, timestamp.
- Team 2: how many retests before Path B escalates to the instructor?
- Team 2: when a revised submission passes, does it come back through the router again?
- Everyone: the message doc has an "aiUseScore" in getReportInfo and onPassPathA. What is that supposed to be, and where does the number come from?
