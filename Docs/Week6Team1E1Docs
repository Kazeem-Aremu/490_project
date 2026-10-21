# Team 1 Week 6 Documents - E1 Role
Jossie Gates - Team 1 - Week 6 - October 2nd, 2026
## Part 1: Integration Plan

**Objective: Explain how each workflow in Team 1 will contribute to a vertical slice of the 
AI-Assisted Assignment Understanding and Authenticity Review System.**

### The Workstreams

**WS1: Identity, student portal, and submission workflow**

Workstream 1 covers login roles, assignment selection, upload validation, submission/version record, 
student status, and entry experience. 
It gathers the submission ID, user ID, assignment ID, and file information. 

**WS2: Assignment configuration, deterministic evaluator, and router**

Workstream 2 covers instructor configuration, secure execution/test harness, sanitized diagnostics, 
correctness decision, PASS/FAIL routing, and evaluator versioning. 
Submission details from WS1 are needed to create the report. 
Evaluation results and route decision are produced here. 

**WS3: AI question planning, generation, and guardrails** 

Workstream 3 is over learning-outcome coverage, prompt/API adapter, grounded question schema, 
prompt/version records, and relevance and leakage controls 

**WS4: Interactive review, scoring, retry, and stop/escalation logic**

Workstream 4 is over session state, response capture, scoring rubric, materially different retry questions, 
completion maximum/inconclusive/escalation behavior, and student results. 

**WS5: Instructor evidence, database/audit, and shared integration**

Workstream 5 is over the operational data model, dashboard/review/override/export, the audit trail, 
interface support for Team 2, and release/deployment documentation. 
Route decisions from WS2 are needed here to create questions. 
WS5 produces a stored evaluation record for the instructor to see.

**Data Flow**

Student -> Login (WS1) -> Upload (WS1) -> Evaluation (WS2) -> Routing Path A/B (WS2) -> Storage 
(WS5) 

## Part 2: Dependency Board
| Workstream | Depends On | Explanation |
| :--- | :--- | :--- |
| 1 | Assignment Configuration | Depends on which assignment the student selects |
| 2 | WS1 Output | Evaluation and routing depend on the submitted assignment. |
| 3 | WS2 Output | Questions depend on assignment context. |
| 4 | WS3 Output | Review evaluation and scoring depend on answers to the questions. |
| 5 | WS2 Output | Needs route decision |

## Part 3: Merge/Branch Assignments 
**Integration Order:**
|Step | Workstream |  Owner |
| :--- | :--- | :--- |
| 1 | 1 - Identity, student portal, and submission workflow. | Garrick |
| 2 | 2 - Assignment configuration, deterministic evaluator, and router. | Ayo |
| 3 | 5 - Instructor evidence, database/audit, and shared integration. | Misael |
| 4 | 3 - AI question planning, generation, and guardrails. | Miles |
| 5 | 4 -  Interactive review, scoring, retry, and stop/escalation logic. | Jossie |

## Part 4: End-to-End Demo Sequence 

Since the workstreams haven’t been created yet, this will be a walkthrough of how the demo should work. 

**Steps:**

**1)** Student logs into the software and has access to the dashboard and their options (WS1) 

**2)** Student selects an assignment and uploads their submission, either by file or copy/paste (WS1). 

**3)** A submission record is saved(WS1). 

**4)** The AI evaluator evaluates the submission and determines it a PASS based on the rubric (WS2, Path A. Team 2 is Path B: FAIL submission).

**5)** The evaluation is stored (WS5). 

**6)** The evaluation result is shared with the student (WS5). 

**These next steps may not be possible in the first demo and can be mocked.**

**7)** Questions are generated for the student to answer (WS3). 

**8)** The student answers, and the AI evaluator evaluates the answer and tracks if the question limit 
has been reached (WS4).
