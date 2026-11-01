import socket
import json

HOST = "127.0.0.1"
PORT = 8342

base = {"submissionID": "1", "uploadValid": "true", "compileStatus": "SUCCESS",
        "testsPassed": "5", "testsTotal": "5", "threshold": "5"}

cases = [
    ("good code, 5 of 5 tests", base),
    ("buggy code, 3 of 5 tests", {**base, "testsPassed": "3"}),
    ("code timed out", {**base, "errorStatus": "TIMEOUT"}),
    ("bad upload (.txt)", {**base, "uploadValid": "false"}),
    ("evaluator crashed", {**base, "errorStatus": "CRASH"}),
]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))
    print("server says:", json.loads(sock.recv(1024).decode("utf-8")))
    sock.sendall(json.dumps({"ack": "ok"}).encode("utf-8"))
    for name, params in cases:
        msg = {"MESSAGE": {"METHOD": "POST", "INFO": "routeSubmission", "PARAMS": params}}
        sock.sendall(json.dumps(msg).encode("utf-8"))
        reply = json.loads(sock.recv(4096).decode("utf-8"))["MESSAGE"]
        print(f"{name:28} -> {reply['route']:14} next path: {reply['nextPath']:10} ({reply['reason']})")
