# Release Notes v1 (Weeks 1-5)

**Project:** AI-Assisted Assignment Understanding Review System (Team 1, CSDP 490)
**Type:** Planning and requirements release. No working software yet.

## Summary

Version 1 covers the first five weeks: understanding the problem, setting up the team, and choosing the requirements and architecture. The prototype and tested code start in version 2.

## Product goal

A platform that verifies real understanding behind passed submissions and guides failed ones through progressive hints and revision cycles, escalating to instructors only when repeated attempts fail.

## What is included

- **Team setup:** roles assigned and five stable workstreams defined (WS1 to WS5), covering workflow design, router rules, the AI review path, session state, and the database and audit trail.
- **Requirements baseline:** requirements and architecture chosen and agreed as the starting point for the design.
- **Two student paths:**
  - **Path A:** a submission that passes the checks goes to an AI understanding review, where the student answers questions.
  - **Path B:** a submission that fails goes to guided correction.
- **Rules settled in the requirements Q&A:**
  - The reference solution never goes to the AI.
  - The instructor owns the rubric.
  - Manual review goes to the instructor queue.
- **Architecture selected** (components as documented in Week 7): student web UI (React/TypeScript), evaluator, router, Path A question session, AI API, and a Supabase database for evaluation records and the audit log.

## Known limits

- No prototype, tested code, or demo yet.
- The evaluator, the AI API, and the retest limit are not decided.

## Next (version 2)

Design models (UML), router rules as tested code, a first working prototype, and the data design.
