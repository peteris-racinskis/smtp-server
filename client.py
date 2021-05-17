from threading import Thread
import socket
from time import sleep

class ClientThread(Thread):

    def __init__(self,dest,msg_q,log_q,**kwargs):
        super().__init__(**kwargs)
        self.dest = dest
        self.q = msg_q
        self.log_q = log_q
        self.hostname = socket.gethostname()
        self.callbacks = [
            self.helo,
            self.mfrm,
            self.rcpt,
            self.data,
            self.quit
        ]
    
    def run(self):
        while True:
            if self.q.empty():
                sleep(0.1)
            else:
                while not self.q.empty():
                    df = self.q.get()
                    self.log(df)
                    self.send_mail(df)

    def log(self,entry):
        self.log_q.put(entry)

    def send_mail(self,df):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                self.log("C: connecting...")
                s.connect(self.dest)
                reply = s.recv(1024)
                self.log("C: reply = " + str(reply,encoding='ascii'))
                if reply:
                    res = str(reply,encoding='ascii').startswith('220')
                procedure = 0
                while res and procedure < len(self.callbacks):
                    res = self.callbacks[procedure](s,df)
                    procedure = procedure + 1
        except Exception as e:
            self.log(e)
    
    def status_ok(self,msg):
        self.log("C: received: " + msg)
        return msg.startswith('250')
    
    def data_reply(self,msg):
        self.log("C: received: " + msg)
        return msg.startswith('354')
    
    def quit_reply(self,msg):
        self.log("C: received: " + msg)
        return msg.startswith('221')

    def send_msg(self, s, msg, data=False, quit=False):
        self.log("C:sending: " + msg)
        msg = bytes(msg, encoding='ascii')
        s.sendall(msg)
        reply = s.recv(1024)
        if not reply:
            return False
        reply = str(reply, encoding='ascii')
        if data:
            return self.data_reply(reply)
        if quit:
            return self.quit_reply(reply)
        return self.status_ok(reply)

    def helo(self, s, _):
        msg = "helo {}\r\n".format(self.hostname)
        return self.send_msg(s,msg)

    def mfrm(self, s, df):
        msg = "mail from:<{}>\r\n".format(df.source.literal)
        return self.send_msg(s,msg)
    
    def rcpt(self, s, df):
        for r in df.rcpts:
            msg = "rcpt to:<{}>\r\n".format(r.literal)
            ret = self.send_msg(s, msg)
            if not ret:
                return False
        msg = "data\r\n"
        return self.send_msg(s, msg, data=True)
    
    def data(self, s, df):
        msg = ''.join(df.data) + '.\r\n'
        return self.send_msg(s, msg)
    
    def quit(self, s, _):
        msg = 'quit\r\n'
        return self.send_msg(s, msg, quit=True)
        

    

