import socket
import json
test_msg = {"Response Code":"200", "MESSAGE":{"METHOD": "GET", "INFO": "userInfo"}}
HOST = "127.0.0.1"
PORT = 8342
MESSAGE_FORMAT = {"Response Code":"200", "MESSAGE":{"KEY1": "message sent"}}
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))

    msg = {"MESSAGE": "hello"}
    sock.sendall(json.dumps(msg).encode("utf-8"))
    reply = sock.recv(1024)
    print(json.loads(reply.decode("utf-8")))

    sock.sendall(json.dumps(test_msg).encode("utf-8"))
    reply = sock.recv(1024)
    print(json.loads(reply.decode("utf-8")))