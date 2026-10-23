import socket
import json
import threading
from DataBaseHandler import DataBaseHandler
#HOST = "127.0.0.1"
#PORT = 8342
hostname = socket.socket()
#MESSAGE_FORMAT = {"Response Code":"200", "MESSAGE":{"METHOD": "message sent"}}

test_response = {"Response Code":"200", "MESSAGE":{"METHOD": "message sent"}}

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
            client_thread = threading.Thread(target=self.handle_Client,args = (client_socket, client_addr))
            client_thread.daemon = True
            client_thread.start()

    ## this function will emit the messages between client and server
    def emit(self, content, socket, addr):
        print(f"[{addr}] Emmiting message {content}")
        formatContent = json.dumps(content).encode("utf-8")
        socket.sendall(formatContent)
    """
    Here is where you will likely need to make changes to endpoints and features
    So far it Each connection creates its own thread the the server services independently. 
    """

   
    def handle_Client(self, client_socket, client_addr ):
        print(f"Connected to {client_addr}")
        with client_socket:
            handshake = json.dumps(self.handshakeMsg).encode("utf-8")
            client_socket.sendall(handshake)
            handshake_reply_raw = client_socket.recv(1024)
            
            while True:
                raw = client_socket.recv(1024)
                if not raw:
                    break
                try:
                    data = json.loads(raw.decode("utf-8"))
                except json.JSONDecodeErrorError as e:
                    reply = {"Response Code": "400", "MESSAGE": {"error":f"Invalid JSON: {e}"}}
                    client_socket.sendall(json.dumps(reply).encode("utf-8"))
                    continue

                if not data: 
                    break
                try: 
                    #message here should be in the format = {"Response Code":"200", "MESSAGE":{"METHOD": "GET", "INFO": nameofInforequest}}
                    if data["MESSAGE"]["METHOD"] == "GET":
                        if data["MESSAGE"]["INFO"] == "userInfo":
                            print("received userinfo request")
                            try: 
                                user_id_raw = data["MESSAGE"]["INFO"]["USERID"]
                                response = self.database.getUser(int(user_id_raw))
                            except ValueError:
                                print(f"ERROR in /getUser: {e}")
                                response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                            finally:
                                self.emit(response,client_socket, client_addr )

                        elif data["MESSAGE"]["INFO"] == "AssignmentInfo":
                            if data["MESSAGE"]["BY"] == "CourseID":
                                try:
                                    print("Getting AssignmentInfo by CourseID")
                                    course_id_raw = data["MESSAGE"]["INFO"]["COURSEID"]
                                    response = self.database.getAssignmentByCourse(int(course_id_raw))
                                except ValueError as e:
                                    print(f"ERROR in get assignment by course: {e}")
                                    response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                                finally:
                                    self.emit(response, client_socket, client_addr)
                            elif data["MESSAGE"]["BY"] == "AssignmentId":
                                try:
                                    print("Getting AssignmentInfo by AssignmetID")
                                    Assignment_id_raw = data["MESSAGE"]["INFO"]["ASSIGNMENTID"]
                                    response = self.database.getAssignment(int(Assignment_id_raw))
                                except ValueError as e:
                                    print(f"ERROR in /getAssignment by ID: {e}")
                                    response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                                finally:
                                    self.emit(response, client_socket, client_addr)
                        elif data["MESSAGE"]["INFO"] == "getCourseInfo":
                            if data["MESSAGE"]["BY"] == "teacherID":
                                try:
                                    print("Getting Course info By teacherID")
                                    teacher_Id_Raw = data["MESSAGE"]["INFO"]["teacherID"]
                                    response = self.database.getCourseByTeacher(int(teacher_Id_Raw))
                                except ValueError as e:
                                    print(f"ERROR in get course by teacher id: {e}")
                                    response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}

                                finally:
                                    self.emit(response, client_socket, client_addr)
                                
                            elif data["MESSAGE"]["INFO"] == "CourseID":
                                try: 
                                    print("Getting Course info by teacherID")
                                    course_id_raw = data["MESSAGE"]["INFO"]["CourseID"]
                                    response = self.database.getCoursebyId(int(course_id_raw))
                                except ValueError as e: 
                                    print(f"ERROR in get course by course id: {e}")
                                    response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                                finally:
                                    self.emit(response, client_socket, client_addr)
                        elif data["MESSAGE"]["INFO"] == "reportInfo":
                            pass
                        elif data["MESSAGE"]["INFO"] == "Enrollement":
                            if data["MESSAGE"]["BY"] == "Course":
                                try: 
                                    print("getting Enrollment info by the course ID")
                                    course_id_raw = data["MESSAGE"]["INFO"]["CourseID"]
                                    response = self.database.getEnrollmentByCourse(int(course_id_raw))
                                except ValueError as e:
                                    print(f"ERROR in get enrollement by course id: {e}")
                                    response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                                finally:
                                    self.emit(response, client_socket, client_socket)

                            elif data["MESSAGE"]["BY"] == "UserID":
                                try: 
                                    print("getting Enrollment info by the user id")
                                    user_id_raw = data["MESSAGE"]["INFO"]["userID"]
                                    response = self.database.getEnrollmentByUser(int(user_id_raw))
                                except ValueError as e:
                                    print(f"ERROR in get enrollment by course id: {e}")
                                    response = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                                finally:
                                    self.emit(response, client_socket, client_socket) 
                        elif data["MESSAGE"]["INFO"] == "getAiConversation":
                            pass
                        else:
                            reply = {"Response Code":"400", "MESSAGE":{"ERROR": "Invalid Get Request", "original Message": data}}
                            self.emit(reply, client_socket, client_addr, client_addr)

                    elif data["MESSAGE"]["METHOD"] == "POST":
                        pass

                except Exception as e:
                    #later send a 500 error code to client
                    print(f"Error receiving message: {e}")
        
def main():
    server = Server()
    server.start()


if __name__ == "__main__":
    main()