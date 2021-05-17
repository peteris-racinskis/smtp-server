import socket
from queue import Queue
from server import ServerThread
from client import ClientThread
from threading import Thread
from time import sleep
from typedefs import MailDataFrame

def logger(q):
    while True:
        sleep(0.05)
        if not q.empty():
            r = q.get()
            if isinstance(r, MailDataFrame):
                print(r.data)
            else:
                for i in range(2):
                    if r[-i] in ["\r", "\n"]:
                        r = r[:-i]
                print(r)
            
            
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
        t = ServerThread(cl_skt, msg_q, log_q, daemon=True)
        t.start()
        i = i + 1