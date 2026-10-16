import os
from flask import jsonify
from dotenv import load_dotenv
from supabase import create_client, Client
##Not sure what to do withthese

##Table names 
AI_CONVOS = "AI_Conversations"
ASSIGNMENT = "ASSIGNMENT"
COURSE = "COURSE"
ENROLLMENT = "Enrollment"
SUBMISSION = "Submission"
USER = "USER"

#AI_CONVO Table names
AI_CONVO_ID = "id"
AI_CONVO_CREATED_AT = "created_at"
AI_CONVO_SUBMISSION = "Submission_id"
AI_CONVO_RESPONSES = "Respnses"
AI_CONVO_TOKENS_USED = "Tokens_used"
AI_CONVO_EVAL_SCORE = "Evaluation_score"
AI_CONVO_AI_SCORE = "AI_Score"
#ASSIGNMENT table names
ASSIGNMENT_ID = "id"
ASSIGNMENT_CREATED = "created_at"
ASSIGNMENT_COURSE_ID = "Course_id"
ASSIGNMENT_TEACHER_ID = "Teacher_id"
ASSIGNMENT_RESOURCE_LINK = "resource_link"
ASSIGNMENT_RUBRIK = "rubrik_link"
ASSIGNMENT_DESCRIPTION = "Description"

#COURSE
COURSE_ID = "id"
COURSE_CREATED = "created_at"
COURSE_TEACHER_ID = "Teacher_ID"
COURSE_NAME = "Course_Name"

#ENROLLMENT
ENROLL_COURSE_ID = "Course_id"
ENROLL_STUDENT_ID = "Student_id"
#SUBMISSION
SUB_ID = "8904"
SUB_ASSIGN_ID = "Assign_id"
SUB_STUDENT_ID = "Student_id"
SUB_SUBMISSION_LINK = "Submission_link"
#USER
USER_ID = "id"
USER_CREATED = "CREATED_AT"
USER_NAME = "NAME"
USER_ROLE = "ROLE"




class DataBaseHandler:
    def __init__(self):
        ##initilaizing the Supabase enviornment and importing the Keys so the website can be active
        load_dotenv()
        ##setting keys
        self.url: str = os.environ.get("SUPABASE_URL")
        self.key: str = os.environ.get("SUPABASE_SECRET_KEY")
        self.supabase: Client = create_client(self.url, self.key)


## Getting
    def getUser(self, UserID):
        ###Get data from the user using their ID and create a user object then return it
        ##user will need data need a function that converts the object into a json or other object.
        print(UserID)
        try:
            ## temp = self.supabase.table(tablename).select("*").eq(columnName, value).execute()
            temp = self.supabase.table(USER).select("*").eq(USER_ID,UserID ).execute()
            data =  temp.data if hasattr(temp,"data") else temp
            return data
        except Exception as e:
            return {"error": f"Get User DBH error :{e}"}
    
    def getEnrollmentByUser(self, studentID):
        ##Search the enrollment table for the users classes
        try:
            temp = self.supabase.table(ENROLLMENT).select("*").eq(ENROLL_STUDENT_ID, studentID).execute()
            data = temp.data if hasattr(temp, 'data') else temp
            return data
        except Exception as e:
            return {"Error": f"getEnrollmentByUSer DBH Error: {e}"}

    def getEnrollmentByCourse(self, courseID):
        try:
            temp = self.supabase.table(ENROLLMENT).select("*").eq(ENROLL_COURSE_ID, courseID).execute()
            data = temp.data if hasattr(temp, 'data') else temp
            return data
        except Exception as e:
            return {"Error": f"getEnrollmentByCourse DBH Error: {e}"}
        
    #get courses by teacher
    def getCourseByTeacher(self, teacherID):
        try:
            temp = self.supabase.table(COURSE).select('*').eq(COURSE_TEACHER_ID, teacherID).execute()
            data = temp.data if hasattr(temp, 'data') else temp
        except Exception as e:
            return {"Error": f"getCourseByTeacher DBH Error: {e}"}

    #get Coruses by id / name
    def getCoursebyId(self, courseId):
        try:
            temp = self.supabase.table(COURSE).select('*').eq(COURSE_ID, courseId).execute()
            data = temp.data if hasattr(temp, 'data') else temp            
        except Exception as e:
            return {"Error": f"getCourseById DBH Error: {e}"}
    #get AssignmenetByCourse
    def getAssignmentByCourse(self, courseId):
        try:
            temp = self.supabase.table(ASSIGNMENT).select('*').eq(ASSIGNMENT_COURSE_ID, courseId).execute()
            data = temp.data if hasattr(temp, 'data') else temp                       
        except Exception as e:
            return {"Error": f"getAssignmentByCourse DBH Error: {e}"}

    #get Assignment
    def getAssignment(self, AssignmentId):
        try:
            temp = self.supabase.table(ASSIGNMENT).select('*').eq(ASSIGNMENT_ID, AssignmentId).execute()
            data = temp.data if hasattr(temp, 'data') else temp                       
        except Exception as e:
            return {"Error": f"getAssignment DBH Error: {e}"}
    #get AI_Conversation
    def getAiConversation(self,aiConvoID):
        try:
            temp = self.supabase.table(ASSIGNMENT).select('*').eq(ASSIGNMENT_ID, AssignmentId).execute()
            data = temp.data if hasattr(temp, 'data') else temp                       
        except Exception as e:
            return {"Error": f"getAssignment DBH Error: {e}"}            
    #Get Submission

##Creating 
    def createUser(self,userDataJson):
        try:
            response = self.supabase.table(USER).upsert([userDataJson]).execute()
            return {"data":response.data}
        except Exception as e:
            ##I was uisng this section for mostly bug fixing
            return {"error": f"Create User DBH error :{e}"}

    def createCourse(self, CourseDataJson):
        try: 
            response = self.supabase.table(COURSE).upsert([CourseDataJson]).execute()
            return {"data": response.data}
        except Exception as e:
            return {"error": f"create Course DBH error :{e}"}

    def setEnrollment(self, enrollmentData):
        try: 
            response = self.supabase.table(ENROLLMENT).upsert([enrollmentData]).execute()
            return {"data": response.data}
        except Exception as e:
            return {"error": f"create Course DBH error :{e}"}