# Week 7 Documents - E5

Jossie Gates - Week 7 - E4 - October 15th, 2026 - Not complete

## Part 1: Prompt Schema

**Objective: To describe how the AI will be used in the software through an example.**

**Input:**
* Assignment
* Learning outcome
* Rubric

**AI Prompt (from the code):**
```
“You are an educational assessment assistant.

Assignment:
{assignment_file}

Learning Outcome:
{learning_file}

Rubric:
{rubric_file}

Evaluate whether the assignment is completed correctly according to the rubric and whether the assignment matches the rubric at least 80%. 
Return in JSON format.”
```
**Expected Output (inside the code):** 
```
{The assignment matches the rubric at least 80%.}
```

**–Update session state–**


**AI Prompt (from code; Path A):**
```
“Generate these based on the assignment and rubric:
1. One conceptual question
2. One implementation question
3. One debugging question

Display these questions one at a time, and evaluate the student’s answer to the questions on a scale of 1-5 based on how well you believe the student shows understanding.
If the score returns under 3, ask them one similar question as a retry. If the answer to the retry falls under 3, go to the next question.
Return in JSON format.”
```

**–Update session state to store questions–**


**Expected output (shown to student):**
```
{Questions for understanding. Question 1: …}
```
**–Student answers–**

**–Update session state to store student answers and score–**


**What could the session state store?**

* Session ID
* User ID
* Assignment ID
* Current question
* Retry number
* Attempt number
* Previous questions
* Scores
* Status: Active/Retry/Escalated
* Tokens used (?)


## Part 2: Versioned Prompts
_By using Claude online, I could try prompts and see which one gave me the response I was looking for._

### Prompt version 1

“You are an educational assessment assistant. Learning outcome: understanding how different Python selection structures work. Generate one conceptual question, one implementation question, and one debugging question.”

**Output:**
Claude generated 3 questions, each with multiple parts.

One question as an example:

```
Python Selection Structures: Assessment
Question 1: Conceptual
Consider the following two code fragments, which both receive a score between 0 and 100:

Fragment A

if score >= 90:
    grade = "A"
if score >= 80:
    grade = "B"
if score >= 70:
    grade = "C"

Fragment B

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"

a) For score = 95, state the final value of grade in each fragment.

b) Explain why the two fragments behave differently, referring to how Python evaluates a series of independent if statements versus an if/elif chain.

c) Describe one situation where using separate if statements is the correct choice instead of elif.
```

_After this output, I used an example assignment, learning outcomes and a rubric to give to Claude to use as a reference. I also asked Claude to condense the questions and ask them one at a time._


### Prompt version 2
"You are an educational assessment assistant.
Attached are the assignment instructions, the learning outcome, the rubric, and the student's submission.

Evaluate whether the assignment is completed correctly according to the rubric and whether the assignment matches the rubric at least 80%. 
Return in JSON format."

_All parts submitted to Claude were in PDF format_

**Claude response:**
```
{
  "student": "Jane Williams", 
  "assignment": "Assignment 1: Python Match-Case Menu System",
  "total_score": 26,
  "max_score": 30,
  "percentage": 86.7,
  "meets_80_percent_threshold": true,
  "overall_verdict": "Mostly complete and meets the 80% threshold. Two assignment requirements were missed: the menu has only 3 options (at least 4 required) and the header has no assignment number.",
  "criteria": [
    {
      "criterion": "Comment at the top of the program", 
      "score": 4,
      "max": 5,
      "level": "Good",
      "feedback": "The header is commented out and includes name, class title (CSDP 112), date, and a short description. The assignment number is missing, so one detail is absent."
    },
    
    {
      "criterion": "Match-Case Usage", 
      "score": 5,
      "max": 5,
      "level": "Excellent",
      "feedback": "Uses match-case with string literal patterns that correctly compare against the input() value, plus a wildcard case. The submitted text lost its indentation, so indentation could not be checked."
    },
    
    {
      "criterion": "Menu Functionality", 
      "score": 4,
      "max": 5,
      "level": "Good",
      "feedback": "All three displayed options (Deposit, Withdraw, Check Balance) respond appropriately. The assignment requires at least four options, so one is missing (e.g., an Exit option)."
    },
    
    {
      "criterion": "Input Handling", 
      "score": 4,
      "max": 5,
      "level": "Good",
      "feedback": "Input is read as a string and matched against string cases, so valid and invalid entries are handled without errors. Minor issue: there is no input cleanup (e.g., input().strip()), so an entry like ' 1' is treated as invalid."
    },
    
    {
      "criterion": "Default Case", 
      "score": 5,
      "max": 5,
      "level": "Excellent",
      "feedback": "case _ properly catches invalid selections and prints 'Invalid Option'."
    },
    
    {
      "criterion": "Code Readability", 
      "score": 4,
      "max": 5,
      "level": "Good",
      "feedback": "The code is short, clear, and has a header comment. It has no inline comments explaining the menu display, input, or match-case sections."
    }
  ],
  
  "requirements_checklist": {
    "header_comment_with_all_details": false,
    "menu_with_at_least_four_options": false,
    "accepts_user_input": true,
    "uses_match_case": true,
    "response_for_each_menu_option": true,
    "default_case_for_invalid_input": true
  },
  
  
  "recommendations": [
    "Add an assignment number to the header comment (e.g., '#Assignment 1').",
    "Add a fourth menu option, such as '4. Exit', with a matching case.",
    "Consider using input().strip() to tolerate stray whitespace.",
    "Add brief inline comments for the menu, input, and match-case sections."
  ]
}
```
