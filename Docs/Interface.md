# Interface Description

This document proposes and details the interfaces between the different pages and systems within our application. There is an attempt to separate the project into a distinct Model-View-Presenter architecture.

# Server
 ### Team 2/1
1. OnLogin 

This function accepts the login cookie and/or the UID and then uses them to get basic account information from the database to send back to the client.

    - Parameters
        - login Cookie/UID
    - Outputs
        -Basic User Account info
            - UID
            - Name
            - Course Name
            - Course Code


2. getDashboard

This function responds to the client’s request by sending a basic list of course info and assignment names.

    - parameters
        - UID
    - Outputs
        - List of Course Info
            - Course Progress
            - Teacher Name
            - List of assignments
                - Name of assignment
                - Due Date

3. uploadAssignment 

This functuion takes uploaded assignments and stores them in Supabase's storage options.

    - Parameters
        -This path allows teachers to upload an assignment and send it to the server for storage in the database..
    - Parameters
        - Assignment File(DOCX, PDF)
        - Assignment Info
            - Assignment Name
            - Due Date
            - Extra Details for prompt
    - Output
        - Saves the Assignmenet File to storage
        - Links the assignment link in the database with the rest of the information.

4. UploadSubmission

This function lets students submit their assignments.
   
    - Parameters
        - Submission Files(.Py, .txt, Etc)
        - UID
    - Outputs
        - Save submission File to the storage
        - Saves a link to the resource in the assignment’s database entry.

6. getAssignment

The server gets the assignment record from the database.

    - Parameters
        - AssignmentID, CourseID
    - Outputs 
        - record of the assignment and potential submission Records.


6. GetReportInfo

This function requests detailed report information from the Server to display to the user.

    - Parameters
        - Course ID
        - UID 
        - Assignment ID

7. SendMessage

Receives messages from the client and sends it to the AI API.

    - Parameters
        - Message from User
        - TimeStamp
        - Attachments
    - Output to API
        - Message from User
        - TimeStamp
        - Attachments

8. getMessage

Gets the message response from the AI API

    - Parameters
        - Message from User
        - TimeStamp
        - Attachments
    - output
        - Formatted message from AI

9. onPassPathA

Verifies that the student has finished Path A or reached a stopping point.

    - Parameters
        - PassStatus(true/false)
        - Evaluation
        - if applicable - Chat Log of PathB

10. onPassPathB

Verifies that the student has finished path B  or reached a stopping point.
    
    - Output
        - Verification Status
        - Evaluation 
        - Chat Log of path B
    
# Log-In Page
### Team 2
1. Onlogin

Sends the user’s login either to the server or directly to Supabase for verification. Receives a login cookie in response.

    - Parameters
        - Password
        - UserName
    - Outputs 
        - Login Cookie and/or UserID number (UID) to the server

# Dashboard
### Team 1
1. getDashboard

This function requests the sever to send a general set of assignments and class information without requesting specifics so as not to bloat the client with unnecessary info.

    - Outputs
        - UID to the server

2. getAssignment

This Function allows a user to select an assignment and then receive information about that assignment.

    - Parameters
        - AssignmentID, CourseID

3. UploadAssignment

This path allows teachers to upload an assignment and send it to the server for storage in the database.

    - Parameters
        - Assignment File(DOCX, PDF)
        - Assignment Info
            - Assignment Name
            - Due Date
            - Extra Details for prompt

4. UploadSubmission

This function lets students submit their assignments.

    -Parameters
        - Submission Files(Py, TXT, Etc)
        - UID
        - Course ID

# Report Page
### Team 2
1. GetReportInfo

This function requests detailed report information from the Server to display to the user.

    - Parameters
        - Course ID
        - UID 
        - Assignment ID

# Path A
### Team 1

1. SendMessage

Sends messages to the AI API through the server.

    - Parameters
        - Message from User
        - TimeStamp
        - Attachments

2. getMessage

Gets message response from the AI API

    - output
        - Formatted message from AI


3. onPassPathA

Verifies that student has finished path A or reached a stopping point.

    - Parameters
        - PassStatus(true/False)
        - Evaluation 

# Path B
### Team 2

1. SendMessage

Sends messages to the AI API through the server.

    - Parameters
        - Message from User
        - TimeStamp
        - Attachments

2. getMessage

gets message response from the AI API

    - output
        - Formated message from AI

3. onPassPathB

Verifies that student has finished path B or reached a stopping point.

    - Parameters
        - PassStatus(true/False)
        - Evaluation 
