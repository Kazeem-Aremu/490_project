from DataBaseHandler import DataBaseHandler
import time
import json
handler = DataBaseHandler()

testAdmin = {
            "id":"1234", 
             "NAME":"John Doe", 
             "ROLE": "ADMIN"
             }
testStudent = {
    "id":"4321", 
    "NAME":"Jane Doe", 
    "ROLE": "Student"
    }
testTeacher = {
    "id":"2341"
    , "NAME":"Bill Smith"
    , "ROLE": "Teacher"
    }

testCourse = {
    "id": "9876"
    , "Teacher_ID": testTeacher["id"]
    , "Course_Name":"TestCourse"
    }
testEnroll = {
    "Course_id": testCourse["id"]
    , "Student_id": testStudent["id"]
    }

testAssignment =  {
    "id": "3421"
    , "Course_id":testCourse["id"]
    , "Teacher_id":testTeacher["id"]
    , "resource_link":"TestUrl.com"
    , "rubrik_link":"RubrikUrl.com"
    , "Description":"description description"}

testSubmission ={
    "id": "8765",
    "Assign_id":testAssignment["id"],
    "Student_id":testStudent["id"],
    "Submission_link":"submissionLink.com"
} 
testAiConvo = {
    "id":"3190",
    "Submission_id":testSubmission["id"],
    "responses":"Hello AI. Hello User",
    "Tokens_used":"1452",
    "Evaluation_score": "80",
    "AI_Score":"10"
}
##Creating the entities
try: 
    print(handler.createUser(testAdmin))

except Exception as e:
    print("Error in /createUser: ", e)

try: 
    print(handler.createUser(testStudent))

except Exception as e:
    print("Error in /createUser: ", e)

try: 
    print(handler.createUser(testTeacher))

except Exception as e:
    print("Error in /createUser: ", e)

##Creating the test course
try:
    print(handler.createCourse(testCourse))

except Exception as e:
    print("Error in /createCourse: ", e)

##Test Enrolling the student:
try: 
    print(handler.setEnrollment(testEnroll))
except Exception as e:
    print("Error in /setEnrollment: ", e)


#Getting the entities
try:
    #get admin
    print(handler.getUser(testAdmin["id"]))
except Exception as e:
    print("error in /getUser", e)


try:
    #get student
    print(handler.getUser(testStudent["id"]))
except Exception as e:
    print("error in /getUser", e)

try:
    #get Teacher 
    print(handler.getUser(testTeacher["id"]))
except Exception as e:
    print("error in /getUser", e)

try:
    ##Getting course
    print(handler.getCourse(testCourse["id"]))
except Exception as e:
    print("error in /getCourse", e)


try:
    ##geting Enrolment by student
    print(handler.getEnrollmentByUser(testStudent["id"]))
except Exception as e:
    print("error in /getEnrollmentbyUser", e)

try:
    ##geting Enrolment by Course
    print(handler.getEnrollmentByCourse(testCourse["id"]))
except Exception as e:
    print("error in /getEnrollmentbyCourse", e)