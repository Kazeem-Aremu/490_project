# Release Notes v2 (Weeks 6-10)

**Project:** AI-Assisted Assignment Understanding Review System (Team 1, CSDP 490)
**Type:** Design baseline and prototype release.

## Summary

Version 2 turns the plan into design models, tested router code, and a working prototype (v0.1) that passes all five demo scenarios. The evaluator and the AI are still simulated.

## What is new

### Router (tested code)
- Rules that sort every submission into **PASS**, **FAIL**, or **MANUAL_REVIEW**, with a reason code for each.
- Passes 11 of 11 labeled sample cases.
- A timeout caused by student code is a FAIL, not a manual review.
- Minor issues, such as missing comments, pass with a warning for the instructor.
- The AI never decides correctness.
- Router is now wired into the prototype (Weeks 9-10); contract v0.2 is drafted.

### Design models
- Path A state machine: planning, asking, awaiting answer, scoring, retry, referred, complete, error, and manual review.
- Sequence diagrams for the full Path A workflow and for a pass path with one retry.
- Evaluation record (data model): one record per submission, shared by Path A and failure diagnosis. Hidden tests, expected outputs, and secrets are never stored.
- Database design for Path A: three tables (Submissions, Evaluations, Interview evidence) linked by submission ID.

### Path A document
- Question types, 7 guardrails, a scoring rubric, and a draft system prompt.
- A logged sample AI run that scores answers as Demonstrated, Partial, or Not Demonstrated.

### Project control
- Schedule baseline, a risk register with 6 risks, an interface register (6 interfaces), and a change log.
- Acceptance and traceability baseline, and a re-prioritized backlog.

### Prototype v0.1
- Real: three login roles, upload checks, routing from check results, instructor records, and an audit log.
- Five demo scenarios, all as expected:
  1. Happy path: correct file passes and Path A starts.
  2. Fail path: a file with a bug fails and goes to guided correction.
  3. Evaluator down: work is saved and sent to manual review, not marked wrong.
  4. AI down: a passing file goes to manual review.
  5. Bad upload: a non-code file is rejected and no attempt is saved.

## Real vs simulated

| Part | Status |
|---|---|
| Login, upload checks, routing, instructor records, audit log | Real |
| Router rules | Tested code, now in the prototype |
| Evaluator | Simulated (reads text patterns, does not run code) |
| AI questions | Simulated (fixed question bank scored by keywords) |
| Path B hints | Mocked |
| Database tables for Path A records | Designed, not yet verified with saved records |

## Known limits

- The evaluator does not run code, so a program written to look right could pass.
- Open checks: records are saved with attempt number and time, and hidden tests never reach the AI.
- Router contract is not agreed yet, and the retest limit is unconfirmed.
- AI API and credentials are not chosen (leaning toward Claude).

## Next

Real evaluator that runs code, AI API decision, the two open checks, the final demo dataset, build and config scripts, then alpha testing in Weeks 11-12.
