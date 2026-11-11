import socket
import json
import threading
import traceback
import os
from urllib.parse import urlparse

from DataBaseHandler import DataBaseHandler
from AIService import AIService, make_submission_fetcher
from AgentInterface import Teacher
from SubmissionService import SubmissionService
from TeacherService import TeacherService
from AssignmentService import AssignmentService

#HOST = "127.0.0.1"
#PORT = 8342
hostname = socket.socket()
_decoder = json.JSONDecoder()


test_response = {"Response Code":"200", "MESSAGE":{"METHOD": "message sent"}}

# POST_ROUTES = {
#     "startAIConversation": "start_coversation",
#     "sendAIMessage":"send_message"
# }

# (INFO, BY) -> (DatabaseHandler method, key to read from MESSAGE["PARAMS"])
GET_ROUTES = {
    ("userInfo", None):                  ("getUser",               "USERID"),
    ("AssignmentInfo", "CourseID"):      ("getAssignmentByCourse", "COURSEID"),
    ("AssignmentInfo", "AssignmentId"):  ("getAssignment",         "ASSIGNMENTID"),
    ("getCourseInfo", "teacherID"):      ("getCourseByTeacher",    "teacherID"),
    ("getCourseInfo", "CourseID"):       ("getCoursebyId",         "CourseID"),
    ("Enrollement", "Course"):           ("getEnrollmentByCourse", "CourseID"),
    ("Enrollement", "UserID"):           ("getEnrollmentByUser",   "userID"),
}


SINGLE_ITEM = {"getUser", "getCoursebyId", "getAssignment"}

NOT_IMPLEMENTED_INFO = {"reportInfo"}
class Server():
    def __init__(self):
        self.HOST = "127.0.0.1"
        self.PORT = 8342
        #self.hostname = socket.socket()
        self.server_socket = None
        self.handshakeMsg = {"Response Code":"200", "MESSAGE":{"HANDSHAKE": "True"}}
        self.database = DataBaseHandler()

        supabase_url = os.environ.get("SUPABASE_URL", "")
        supabase_host = urlparse(supabase_url).hostname
        ## lets the AI tutor read submission files kept in private Supabase Storage
        storage_key = os.environ.get("SUPABASE_SECRET_KEY", "")
        storage_headers = {"apikey": storage_key, "Authorization": f"Bearer {storage_key}"}
        self.submissions = SubmissionService(self.database, supabase_url)
        self.teachers = TeacherService(self.database)
        self.assignments = AssignmentService(self.database, supabase_url, self.teachers)
        ## the tutor also gets the text of the teacher's assignment sheet and rubric
        self.ai = AIService(self.database, fetch_text=make_submission_fetcher(supabase_host, storage_headers),
                            assignment_texts=self.assignments.assignment_texts)


    ##this function is called and starts up the server
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if os.name != "nt":
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(f"Socket created on {self.HOST}:{self.PORT}")
        try:
            self.server_socket.bind((self.HOST, self.PORT))

        except socket.error as e:
            print(f"Binding failed: {e}")
            return

        ## allows 5 connections to be wait listed
        self.server_socket.listen(5)
        print(f"Listening on {self.HOST}:{self.PORT}")
        while True:
            client_socket, client_addr = self.server_socket.accept()
            print(f"Connected to {client_addr}, starting thread")
            client_thread = threading.Thread(
                target=self.handle_Client,
                args = (client_socket, client_addr))
            client_thread.daemon = True
            client_thread.start()

    ## this function will emit the messages between client and server
    def emit(self, content, socket, addr):
        print(f"[{addr}] Emitting message {content}")
        formatContent = json.dumps(content, default=str).encode("utf-8") + b"\n"
        socket.sendall(formatContent)

    def read_message(self, sock, buf):
        while True:
            stripped = buf.lstrip()
            if stripped:
                try:
                    text  =stripped.decode("utf-8")
                    obj, end = _decoder.raw_decode(text)
                    return "ok", obj, text[end:].encode("utf-8")
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    if b"\n" in stripped:
                        _, _, rest = stripped.partition(b"\n")
                        return "bad", str(e), rest

            chunk = sock.recv(4096)
            if not chunk: 
                return "closed", None, b""
            buf += chunk

    @staticmethod
    def error(code, text, original = None):
        body = {"ERROR": text}
        if original is not None:
            body["original Message"] = original
        return {"Response Code":code, "MESSAGE":body}

   ## Routing

    def handle_Requests(self, data):
        if not isinstance(data, dict):
            return self.error("400", "Request must be a JSON object", data)

        message = data.get("MESSAGE")
        if not isinstance(message, dict):
            return self.error("400", "Missing MESSAGE object", data)

        method = message.get("METHOD")
        if method == "GET":
            return self.handle_get(message, data)
        if method == "POST":
            return self.handle_post(message, data)
        return self.error("400", f"Uknown or missing METHOD: {method!r}", data)

    @staticmethod
    def int_params(params, *keys):
        try: 
            return tuple(int(params[k]) for k in keys)
        except (KeyError, ValueError, TypeError):
            return None
        
    def handle_post(self, message, original):
        info = message.get("INFO")
        params = message.get("PARAMS")

        if not isinstance(params, dict):
            return self.error("400", "Missing PARAMS", original)
        ##Server parses request AI is in AI service
        if info == "startAIConversation":
            ids = self.int_params(params, "USERID","SUBMISSIONID")
            #text = params.get("TEXT")
            if ids is None:
                return self.error("400", "PARAS needs integer USER and SUBMISSIONID", original)
            return self.ai.start_conversation(ids[0], ids[1])

        if info == "sendAIMessage":
            ids = self.int_params(params, "USERID", "CONVOID")
            if ids is None:
                return self.error("400", "PARAMS needs integer USERID and CONVOID", original)
            return self.ai.send_message(ids[0], ids[1], params.get('TEXT'))

        if info == "createSubmission":
            ids = self.int_params(params, "USERID", "ASSIGNMENTID")
            if ids is None:
                return self.error("400", "PARAMS needs integer USERID and ASSIGNMENTID", original)
            return self.submissions.create_submission(ids[0], ids[1], params.get("NAME"), params.get("CODE"))

        ##Teacher dashboard: new assignment with optional PDF/DOCX assignment sheet and rubric
        if info == "createAssignment":
            ids = self.int_params(params, "USERID", "COURSEID")
            if ids is None:
                return self.error("400", "PARAMS needs integer USERID and COURSEID", original)
            return self.assignments.create_assignment(ids[0], ids[1], params.get("DESCRIPTION"), params.get("FILES"))

        ##Both dashboards: a short-lived link to an assignment's file (KIND "assignment" or "rubric")
        if info == "assignmentFile":
            ids = self.int_params(params, "USERID", "ASSIGNMENTID")
            if ids is None:
                return self.error("400", "PARAMS needs integer USERID and ASSIGNMENTID", original)
            return self.assignments.file_link(ids[0], ids[1], params.get("KIND"))

        ##Teacher dashboard: create a class owned by the signed-in teacher
        if info == "createCourse":
            ids = self.int_params(params, "USERID")
            if ids is None:
                return self.error("400", "PARAMS needs integer USERID and a NAME", original)
            return self.teachers.create_course(ids[0], params.get("NAME"))

        ##Teacher dashboard: add / remove a student from one of the teacher's classes
        if info in ("enrollStudent", "unenrollStudent"):
            ids = self.int_params(params, "USERID", "COURSEID", "STUDENTID")
            if ids is None:
                return self.error("400", "PARAMS needs integer USERID, COURSEID and STUDENTID", original)
            action = self.teachers.enroll if info == "enrollStudent" else self.teachers.unenroll
            return action(*ids)
        return self.error("400", f"Unknown POST request:{info!r}", original)


    def handle_get(self, message, original):
        info = message.get("INFO")
        by = message.get("BY")

        if info in NOT_IMPLEMENTED_INFO:
            return self.error("501", f"{info} not implemented yet", original)

        ##Teacher dashboard: the students a teacher can add to a class
        if info == "StudentList":
            params = message.get("PARAMS")
            ids = self.int_params(params, "USERID") if isinstance(params, dict) else None
            if ids is None:
                return self.error("400", "PARAMS needs integer USERID", original)
            return self.teachers.list_students(ids[0])

        route = GET_ROUTES.get((info, by)) or GET_ROUTES.get((info, None))

        if route is None:
            return self.error("400", f"Invalid GET request (INFO = {info!r}, BY = {by!r})",original)
        db_method, param_key = route

        params = message.get("PARAMS")
        if not isinstance(params, dict) or param_key not in params:
            return self.error("400", f"Missing PARAMS.{param_key}", original)

        try:
            the_id = int(params[param_key])
        except (ValueError, TypeError):
            return self.error("400", f"PARAMS.{param_key} must be an integer", original)

        print(F"GET {info} BY {by} -> {db_method}({the_id})")

        try:
            result = getattr(self.database,db_method)(the_id)
        except Exception as e:
            traceback.print_exc()
            return self.error("500", f"Database error in {db_method}: {e}", original)

        if result is None or (db_method in SINGLE_ITEM and result == []) :
            return self.error("404", "Not found", original)

        if isinstance(result,dict) and "Response Code" in result:
            return result

        return {"Response Code": "200", "MESSAGE": result}

    def handle_Client(self, client_socket, client_addr ):
        print(f"Connected to {client_addr}")
        with client_socket:
            try:
                self.emit(self.handshakeMsg, client_socket, client_addr)
                # handshake = json.dumps(self.handshakeMsg).encode("utf-8")
                # client_socket.sendall(handshake)
                # handshake_reply_raw = client_socket.recv(1024)
                
                status , _, buf = self.read_message(client_socket, b"")
                if status == "closed":
                    return
                
                while True:
                    status, data, buf = self.read_message(client_socket, buf)
                    if status == "closed":
                        break
                    if status == "bad":
                        self.emit(self.error("400", f"Invalid JSON:{data}"), client_socket, client_addr)
                        continue

                    try:
                        response = self.handle_Requests(data)
                    except Exception as e:
                        traceback.print_exc()
                        response = self.error("500", f"Internal Server error: {e}")

                    self.emit(response, client_socket, client_addr)

            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                print(f"{client_addr} disconnected abruptly")

        print(f"Closed {client_addr}")

        
def main():
    server = Server()
    ## browsers cannot open raw TCP sockets, so the student portal talks to this same
    ## server through a WebSocket on port 8343 (see WebSocketServer.py)
    from WebSocketServer import start_in_background
    start_in_background(server)
    server.start()

if __name__ == "__main__":
    main()