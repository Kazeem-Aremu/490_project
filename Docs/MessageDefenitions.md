# Message Dictionary

This document will show the structure of the messages between the systems. This will include key names and example data.

## OnLogin

 - Message: "onLogin"
    - UID: "12345678910"

#### Server Response 

 - Message: "onLogin"
    - UID: "12345678910"
    - userName: "JohnDoe134"

## getDasboard
- Message: "getDasboard"
    - UID: "12345678910"

#### Server Response
- Message: "getDasboard"
    - courseInfo:
        - averageScore: "80"
        - courseName: "CSDP 120"
        - professorName: "Jane Smith"
        - ListofAssignments:
            1. assignmentName: 
                - "Random Number Guessing Game"
                - dueDate: "01/12/28" 
                - AssignmentID: "987654"
            2. ...

## uploadAssignment
- Message: "uploadAssignment"
    - assignmentFile: "randGuessingGame.pdf"
    - assignmentInfo: "This tests the students knowledge of the randint function in python"
    - dueDate: "01/12/28"
    - extraDetails: "make sure that the student formats the output and prompts"

## uploadSubmission
- Message: "uploadSubmission"
    - submissionfile: "randGuessGame_JohnDoe.PY"
    - UID: "12345678910"
    - courseID: "1111"

## getReportInfo

- Message: "getReportInfo"
    - courseID: "1111"
    - UID: "12345678910"
    - AssignmentID: "987654"

#### Server Response
- Message: "getReportInfo"
    - mainReport: "The system judged this submission and found that the following improvements can be made..."
    - qualityScore: "75"
    - aiUseScore: "32"

## sendMessage 

## Client
- Message: "sendMessage"
    - MessageText: "Hello AI, this is my project!"
    - UID
    - Assignment ID


## getMessage

#### server response
- Message: "getMessage"
    - messageFromAI
    - Timestamp

## onPassPathA
- Message: "onPassPathA"
    - passStatus: "true"
    - Evaluation: 
        - reportText: "This assignment displays understanding of course materials..."
        - aiUseScore: "75"
        - qualityScore: "80"

## onPassPathB

#### Server
- Message: "onPassPathB"
    - passStatus: "true"
    - Evaluation: 
        - reportText: "Student has corrected errors and produced working code"
        - chatLogo: this will then be a record of the all chats to be sent to pathA so it can have context.
