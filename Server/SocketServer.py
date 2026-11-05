import socket
import json
import threading
import traceback
from DataBaseHandler import DataBaseHandler
#HOST = "127.0.0.1"
#PORT = 8342
hostname = socket.socket()
_decoder = json.JSONDecoder()


test_response = {"Response Code":"200", "MESSAGE":{"METHOD": "message sent"}}


GET_ROUTES = {
    ("userInfo", None):                  ("getUser",               "USERID"),
    ("AssignmentInfo", "CourseID"):      ("getAssignmentByCourse", "COURSEID"),
    ("AssignmentInfo", "AssignmentId"):  ("getAssignment",         "ASSIGNMENTID"),
    ("getCourseInfo", "teacherID"):      ("getCourseByTeacher",    "teacherID"),
    ("getCourseInfo", "CourseID"):       ("getCoursebyId",         "CourseID"),
    ("Enrollement", "Course"):           ("getEnrollmentByCourse", "CourseID"),
    ("Enrollement", "UserID"):           ("getEnrollmentByUser",   "userID"),
    ("getAIConversation","ConvoID"):       ("getAiConversation", "")
}


SINGLE_ITEM = {"GetUser", "getCoursebyId", "getAssignment"}

NOT_IMPLEMENTED_INFO = {"reportInfo", "getAiConversation"}
class Server():
    def __init__(self):
        self.HOST = "127.0.0.1"
        self.PORT = 8342
        self.hostname = socket.socket()
        self.server_socket = None
        self.handshakeMsg = {"Response Code":"200", "MESSAGE":{"HANDSHAKE": "True"}}
        self.database = DataBaseHandler()


    ##this function is called and starts up the server
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
            return self.error("501", "POST not implemented yet")

        return self.error("400", f"Uknown or missing METHOD: {method!r}", data)


    def handle_get(self, message, original):
        info = message.get("INFO")
        by = message.get("BY")

        if info in NOT_IMPLEMENTED_INFO:
            return self.error("501", f"{info} not implemented yet", original)

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
            return self.error("500", f"Database error in {db_method}: {e}")

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


                ## this code is now redundant saving it for future reference. I try not to delete old code.
                # raw = client_socket.recv(1024)
                # if not raw:
                #     break
                # try:
                #     data = json.loads(raw.decode("utf-8"))
                # except json.JSONDecodeError as e:
                #     reply = {"Response Code": "400", "MESSAGE": {"error":f"Invalid JSON: {e}"}}
                #     client_socket.sendall(json.dumps(reply).encode("utf-8"))
                #     continue

                # if not data: 
                #     break
                # try: 
                #     #message here should be in the format = {"Response Code":"200", "MESSAGE":{"METHOD": "GET", "INFO": nameofInforequest}}
                #     if data["MESSAGE"]["METHOD"] == "GET":
                #         if data["MESSAGE"]["INFO"] == "userInfo":
                #             print("received userinfo request")
                #             try: 
                #                 user_id_raw = data["MESSAGE"]["INFO"]["USERID"]
                #                 response = self.database.getUser(int(user_id_raw))
                #             except ValueError:
                #                 print(f"ERROR in /getUser: {e}")
                #                 response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                #             finally:
                #                 self.emit(response,client_socket, client_addr )

                #         elif data["MESSAGE"]["INFO"] == "AssignmentInfo":
                #             if data["MESSAGE"]["BY"] == "CourseID":
                #                 try:
                #                     print("Getting AssignmentInfo by CourseID")
                #                     course_id_raw = data["MESSAGE"]["INFO"]["COURSEID"]
                #                     response = self.database.getAssignmentByCourse(int(course_id_raw))
                #                 except ValueError as e:
                #                     print(f"ERROR in get assignment by course: {e}")
                #                     response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                #                 finally:
                #                     self.emit(response, client_socket, client_addr)
                #             elif data["MESSAGE"]["BY"] == "AssignmentId":
                #                 try:
                #                     print("Getting AssignmentInfo by AssignmetID")
                #                     Assignment_id_raw = data["MESSAGE"]["INFO"]["ASSIGNMENTID"]
                #                     response = self.database.getAssignment(int(Assignment_id_raw))
                #                 except ValueError as e:
                #                     print(f"ERROR in /getAssignment by ID: {e}")
                #                     response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                #                 finally:
                #                     self.emit(response, client_socket, client_addr)
                #         elif data["MESSAGE"]["INFO"] == "getCourseInfo":
                #             if data["MESSAGE"]["BY"] == "teacherID":
                #                 try:
                #                     print("Getting Course info By teacherID")
                #                     teacher_Id_Raw = data["MESSAGE"]["INFO"]["teacherID"]
                #                     response = self.database.getCourseByTeacher(int(teacher_Id_Raw))
                #                 except ValueError as e:
                #                     print(f"ERROR in get course by teacher id: {e}")
                #                     response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}

                #                 finally:
                #                     self.emit(response, client_socket, client_addr)
                                
                #             elif data["MESSAGE"]["INFO"] == "CourseID":
                #                 try: 
                #                     print("Getting Course info by teacherID")
                #                     course_id_raw = data["MESSAGE"]["INFO"]["CourseID"]
                #                     response = self.database.getCoursebyId(int(course_id_raw))
                #                 except ValueError as e: 
                #                     print(f"ERROR in get course by course id: {e}")
                #                     response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                #                 finally:
                #                     self.emit(response, client_socket, client_addr)
                #         elif data["MESSAGE"]["INFO"] == "reportInfo":
                #             pass
                #         elif data["MESSAGE"]["INFO"] == "Enrollement":
                #             if data["MESSAGE"]["BY"] == "Course":
                #                 try: 
                #                     print("getting Enrollment info by the course ID")
                #                     course_id_raw = data["MESSAGE"]["INFO"]["CourseID"]
                #                     response = self.database.getEnrollmentByCourse(int(course_id_raw))
                #                 except ValueError as e:
                #                     print(f"ERROR in get enrollement by course id: {e}")
                #                     response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                #                 finally:
                #                     self.emit(response, client_socket, client_socket)

                #             elif data["MESSAGE"]["BY"] == "UserID":
                #                 try: 
                #                     print("getting Enrollment info by the user id")
                #                     user_id_raw = data["MESSAGE"]["INFO"]["userID"]
                #                     response = self.database.getEnrollmentByUser(int(user_id_raw))
                #                 except ValueError as e:
                #                     print(f"ERROR in get enrollment by course id: {e}")
                #                     response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                #                 finally:
                #                     self.emit(response, client_socket, client_socket) 
                #         elif data["MESSAGE"]["INFO"] == "getAiConversation":
                #             pass
                #         else:
                #             reply = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                #             self.emit(reply, client_socket, client_addr, client_addr)

                #     elif data["MESSAGE"]["METHOD"] == "POST":
                #         pass

                # except Exception as e:
                #     #later send a 500 error code to client
                #     print(f"Error receiving message: {e}")
        
def main():
    server = Server()
    server.start()


if __name__ == "__main__":
    main()