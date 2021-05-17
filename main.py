import socket
from queue import Queue
from server import ServerThread
from client import ClientThread
from threading import Thread
from time import sleep

def logger(q):
    while True:
        sleep(0.05)
        if not q.empty():
            print(q.get())
            
            
HOST = '127.0.0.1'
SERVPORT = 42069
DESTPORT = 25
BACKLOG = 5
msg_q = Queue()
log_q = Queue()
client_thread = ClientThread((HOST,DESTPORT), msg_q, log_q, daemon=True)
client_thread.start()
log = Thread(target=logger, args=(log_q,), daemon=True)
log.start()

with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
    s.bind((HOST,SERVPORT))
    i = 0
    while True:
        s.listen(BACKLOG)
        cl_skt,addr = s.accept()
        t = ServerThread(cl_skt, msg_q, daemon=True)
        t.start()
        i = i + 1