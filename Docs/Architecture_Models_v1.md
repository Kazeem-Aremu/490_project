# Architecture Models v1 (E3, Week 7)

**Owner:** Portia Ogbuja · **Status:** Draft, needs teammate review

This covers the context, component, and state models, a trace of one failed submission
through the architecture, and the security, privacy, and accessibility design. Faith's
and Osa's sequence diagrams and Nyles's Interface.md already cover the general flow and
the interfaces, so they are not redrawn here. The data model depends on Faith's final
database schema, which isn't set yet.

## 1. Context model

This shows the platform as one box and everything outside it. Team 1's evaluator is the
first stop: it tests every submission and handles the passed ones, including the check
that the student understands their code. Only failed submissions come to the platform,
where Claude writes the hints and Supabase handles sign-in and storage. Instructors
review progress and escalations.

```mermaid
flowchart LR
    Student([Student])
    Instructor([Instructor])
    Team1["<b>Team 1</b><br/>Evaluator / Router<br/>tests every submission"]
    Pass["Team 1 path for passed code<br/>(understanding check)"]
    Platform["<b>Team 2 Platform</b><br/>guides failed submissions"]
    Claude["Claude API"]
    Supa["Supabase<br/>Auth + Postgres"]

    Student -->|submits code| Team1
    Team1 -->|passed| Pass
    Team1 <-->|failed record in,<br/>re-test request out| Platform
    Platform <-->|hints out,<br/>revised code in| Student
    Instructor -->|reviews progress<br/>and escalations| Platform
    Platform <-->|prompt out,<br/>draft hint back| Claude
    Platform <-->|sign-in, store<br/>and read data| Supa

    style Platform fill:#0E1F3D,stroke:#0E1F3D,color:#FFFFFF
    style Pass fill:#FFFFFF,stroke:#2E6F8F,stroke-dasharray: 5 5
```

## 2. Component model

This shows the main parts inside the platform. The workstream tags come from the team's
failed-submission step list. The Hint Validator sits between the AI Service and the
student, and is the new piece from WS3.

```mermaid
flowchart TB
    subgraph FE["React / TypeScript Frontend (WS1)"]
        Login["Login / Sign-up"]
        Dash["Dashboard"]
        Report["Report page"]
    end

    subgraph BE["Backend API"]
        Diag["Failure diagnosis<br/>and mapping (WS2)"]
        Ladder["Feedback ladder<br/>tier selection (WS3)"]
        AI["AI Service wrapper (WS3)"]
        Valid["Hint Validator (WS3)"]
        Rev["Revision and re-test (WS4)"]
        Prog["Progress evidence (WS5)"]
    end

    Team1["Team 1 Evaluator"]
    Claude["Claude API"]
    DB[("Supabase<br/>Auth + Postgres")]

    FE <--> BE
    Team1 --> Diag
    Diag --> Ladder
    Ladder --> AI
    AI <--> Claude
    AI --> Valid
    Valid -->|blocked: regenerate| AI
    Valid -->|approved hint| Report
    Report -->|student resubmits| Rev
    Rev --> Team1
    Rev --> Prog
    BE <--> DB
```

Nyles's Interface.md describes a Model-View-Presenter split. How these boxes map onto
it is still to be confirmed with Nyles.

## 3. State model (a student's submission)

This follows one failed submission through the hint tiers. Each "still failing" arrow
means the student revised, resubmitted, and was re-tested. The number of tiers before
escalation is still an open question for the sponsor, so Tier 3 is shown as the last
tier for now.

```mermaid
stateDiagram-v2
    [*] --> Failed
    Failed --> Tier1: first hint given
    Tier1 --> Tier2: still failing
    Tier2 --> Tier3: still failing
    Tier3 --> Escalated: still failing at max tier
    Tier1 --> Passed: tests pass
    Tier2 --> Passed: tests pass
    Tier3 --> Passed: tests pass
    Passed --> [*]
    Escalated --> [*]
```

## 4. Failed-submission trace (FS-001)

This follows one real failed submission, Faith's test case FS-001, through the
architecture. The student's code returns "Negative" for the input 0 when the expected
result is "Zero", because the code never checks for zero separately.

```mermaid
sequenceDiagram
    actor S as Student
    participant FE as Frontend
    participant BE as Backend API
    participant T1 as Team 1 Evaluator
    participant AI as Claude API
    participant V as Hint Validator
    participant DB as Supabase

    S->>FE: Submits FS-001 code
    FE->>BE: UploadSubmission (file, user ID)
    BE->>T1: Test the code
    T1-->>BE: FAIL, input 0, expected Zero, got Negative
    BE->>BE: Diagnose (missing boundary case), pick Tier 1
    BE->>AI: requestHint (code, failure, Tier 1)
    AI-->>BE: Draft hint
    BE->>V: Check the draft hint
    V-->>BE: Approved
    BE->>DB: Store submission, Tier 1, hint
    BE-->>FE: Hint
    FE-->>S: What happens when the number is neither greater than nor less than zero?
```

| Step | What happens | What is passed |
|---|---|---|
| 1 to 2 | The student submits and the frontend sends it to the backend | The code file and the student's user ID |
| 3 to 4 | Team 1's evaluator tests it and reports the failure | Input 0, expected "Zero", actual "Negative" |
| 5 | The backend works out the failure type and picks the hint tier | Failure type (missing boundary case), attempt 1 means Tier 1 |
| 6 to 7 | The backend asks Claude for a hint | The code, the failure, and the tier. Claude returns a draft hint. |
| 8 to 9 | The Hint Validator checks the draft before anyone sees it | The draft hint, and an approved or blocked result |
| 10 | The backend stores the result in Supabase | The submission, the tier, and the hint |
| 11 to 12 | The hint is shown to the student on the report page | The Tier 1 hint |

If the validator blocks a draft, the backend asks Claude for a new one before anything
reaches the student. The details are in Hint_Validator_Spec.md.

After the hint, the student revises and resubmits, and the same trace repeats from
step 1. If the code still fails, the next attempt moves up a tier.

## 5. Security, privacy, and accessibility design

These are proposals for the team to confirm.

**Security.** The Claude API key stays on the server and never goes into the React
code. Sign-in goes through Supabase Auth, and students should only be able to read
their own submissions and hints, which can be enforced with Supabase's row-level
security.

**Privacy.** Student code is sent to Claude to generate hints, so we should send only
what the hint needs. We still need to read Anthropic's data handling terms to confirm
how that code is stored or used, which hasn't been checked yet. We should also decide
how long hint and validation logs are kept.

**Accessibility.** Hint tiers should be labeled with text and not only color, every
screen should work from the keyboard, and the pink badges need a contrast check against
the white cards.

## 6. Open items

- The exact boundary with Team 1 (who receives the upload, and where passed submissions
  go) needs to be confirmed in the shared contract.
- The Team 1 failed-submission record format isn't final, so the fields in the trace
  are an assumption.
- `requestHint` is a proposed message name. Nyles's Interface.md needs to be checked
  for an existing hint message.
- The failure type label in the trace ("missing boundary case") is only an example
  until the failure taxonomy is final.
- ADR 2 still lists the dashboard library (MUI) as Proposed, while the Week 7 recap says
  Material UI was confirmed. The ADR status needs to be brought up to date.
- No deployment decision has been recorded in the team's slides or ADRs yet.
- Maximum hint tiers before escalation (sponsor question).
- The data model waits on Faith's final schema.
