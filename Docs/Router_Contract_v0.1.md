# Router Contract v0.1 (draft)

Written by Ayo (WS2: evaluator and router). This is a draft so Team 1 and Team 2 can agree on it. Nothing here is final until Team 2 says it's good.

## What this is for

After a student uploads their code, the evaluator runs the tests and the router decides where the submission goes next. This doc says what the router gets, what it sends back, and the rules around it, so the server and Path A / Path B all expect the same thing.

The router only looks at test results and the instructor's rules. The AI is not involved in this step and never decides if the code is correct.

## routeSubmission

Format matches the server messages we already use. All the values in the examples below (IDs, test counts, timestamps) are made-up examples, not real data. The field names are my draft and can change.

### What the router receives

- Message: "routeSubmission"
    - submissionID: "8765"
    - assignmentID: "3421"
    - studentID: "4321"
    - uploadStatus: "ok"  (or "rejected")
    - testsPassed: "5"
    - testsTotal: "5"
    - mandatoryChecksMet: "true"
    - evaluatorStatus: "ok"  (or "error" or "timeout")
    - evaluatorVersion: "v0.1"
    - timestamp: "2026-10-22T13:00:00Z"

### What the router sends back

- Message: "routeSubmission"
    - submissionID: "8765"
    - route: "PASS"  (or "FAIL" or "MANUAL_REVIEW")
    - reason: "all mandatory checks met"
    - countsAsAttempt: "true"
    - nextPath: "A"  (or "B" or "instructor")

### Example of the full message

```json
{
  "Response Code": "200",
  "MESSAGE": {
    "METHOD": "POST",
    "INFO": "routeSubmission",
    "submissionID": "8765",
    "route": "PASS",
    "reason": "all mandatory checks met",
    "countsAsAttempt": "true",
    "nextPath": "A"
  }
}
```

## Where each route goes

| Route | What it means | Goes to |
|---|---|---|
| PASS | All the mandatory checks were met | Path A (understanding questions) |
| FAIL | At least one mandatory check was not met | Path B (guided correction, Team 2) |
| MANUAL_REVIEW | Something went wrong on our side, or the case needs a person | The instructor queue |

## Rules

1. A bad upload (wrong file type, too big, empty) is rejected with a message. It does not count as an attempt and it does not go to Path A or Path B.
2. If the student's code runs too long (a timeout), that is a FAIL. This is our team's decision.
3. If our side breaks, like the evaluator being down, the test suite missing, or something not allowed happening, it goes to MANUAL_REVIEW. The student is never marked wrong because of our problem.
4. Only a PASS starts Path A. The system never says a student cheated.
5. No hidden tests, solutions, or keys are ever in this message. Only the sanitized results listed above.

## Questions I still need answered

- Nyles: what do you want the field names and types to be on your server? I'm happy to rename mine to match.
- Nyles: should the router write the result straight into Supabase, or send it through your server? I think we need a small table for it (submission ID, tests passed and total, route, evaluator version, reason, timestamp).
- Team 2: how many retests before Path B escalates to the instructor?
- Team 2: when a revised submission passes, does it come back through the router again?
- Everyone: the message doc has an "aiUseScore" in getReportInfo and onPassPathA. What is that supposed to be, and where does the number come from?
