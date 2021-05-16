import socket
from queue import Queue
from server import ServerThread
from threading import Thread
from time import sleep


def logger(q):
    while True:
        sleep(0.05)
        if not q.empty():
            df = q.get()
            print("Source:" + df.source.literal)
            print("Recipient list:")
            [print(x.literal) for x in df.rcpts]
            print("Message contents: ")
            print(''.join(df.data))
            

HOST = '127.0.0.1'
PORT = 42069
BACKLOG = 5
### NB: FOR THE LONGEST TIME I WAS  TRACKIGN DOWN AN ERROR 
### queue.Queue -> Queue()!!!!!!!
msg_q = Queue()
log_thread = Thread(target=logger, args=(msg_q,), daemon=True)
log_thread.start()

with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
    s.bind((HOST,PORT))
    i = 0
    while True:
        s.listen(BACKLOG)
        # accept() returns a socket object and a remote addr tuple
        cl_skt,addr = s.accept()
        ### NB: target needs to be function ref; args - a separate iterable!!!
        t = ServerThread(cl_skt, msg_q, daemon=True)
        t.start()
        i = i + 1