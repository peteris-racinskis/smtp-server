from threading import Thread
import socket, re
from typedefs import MailAddress, ServerState, RequestType, MailDataFrame


class ServerThread(Thread):

    # Static variables
    OK      = "250 Ok"
    BYE     = "221 Bye"
    DATA    = "354 terminate with <CRLF>.<CRLF>"
    SYN_ERR = "501 syntax error"
    SEQ_ERR = "503 bad sequence"
    DOM_ERR = "550 address rejected"
    NO_RCPT = "554 no valid recipient"
    rtypes = {
        "HELO"      : RequestType.HELO,
        "EHLO"      : RequestType.HELO, # <- Not sure if have to respond
        "MAIL FROM" : RequestType.FROM,
        "RCPT TO"   : RequestType.RCPT,
        "DATA"      : RequestType.DATA,
        "QUIT"      : RequestType.QUIT,
        "RSET"      : RequestType.RSET,
    }
    domains = [
        "localhost.com",
    ]

    def __init__(self,sock,msg_q,log_q,**kwargs):
        super().__init__(**kwargs)
        self.sock = sock
        self.hostname = socket.gethostname() + ".lan"
        self.q = msg_q
        self.log_q = log_q
        self.df = None
        self.state = ServerState.INIT
        self.WELCOME = "220 {} SMTP ready\n".format(self.hostname)
        self.HELO = "250 {}".format(self.hostname)
        self.noreply = False
        # callbacks not static because need to put self pointer in closure
        self.callbacks = {
            ServerState.INIT : self.init_handler,
            ServerState.RCPT : self.rcpt_handler,
            ServerState.DATA : self.data_handler,
        }
        
    # The super.start() method calls the object's run() <- override that here
    def run(self):
        self.sock.sendall(self.pack(self.WELCOME))
        while True:
            msg = self.sock.recv(4096)
            if not msg:
                break
            self.log("S: Received: " + str(msg, encoding='ascii'))
            reply = self.handle_request(msg) + '\r\n'
            if not self.noreply:
                self.sock.sendall(self.pack(reply))
            if self.state == ServerState.QUIT:
                break
        self.sock.close()

    def pack(self,s):
        return bytes(s, encoding='ascii')

    def log(self,entry):
        self.log_q.put(entry)

    def handle_request(self,msg):
        msg = str(msg, encoding='ascii')
        rtype, msg = self.request_type(msg)
        if rtype == RequestType.QUIT:
            reply = self.BYE
            self.state = ServerState.QUIT
        elif rtype == RequestType.RSET:
            reply = self.OK
            self.state = ServerState.INIT
            self.df = None
        else:
            reply = self.callbacks[self.state](msg,rtype)
        return reply

    def request_type(self,msg):
        rtype = RequestType.FAIL
        for k,v in self.rtypes.items():
            if msg.upper().startswith(k):
                rtype = v
                break
        if self.state == ServerState.DATA:
            terminate, msg = self.terminate_data(msg)
            if terminate: rtype = RequestType.TERM
            else: rtype = RequestType.LINE
        return rtype, msg

    def terminate_data(self,s):
        # (^|\r\n)  <- string start or previous line <CRLF>
        # \.        <- literal '.'
        # \r\n      <- literal <CRLF>
        pattern = re.compile(r'(^|\r\n)\.\r\n')
        m = re.search(pattern,s)  # only finds the first occurrence
        terminate = False
        if m:
            terminate = True
            s = s[:m.end()-3]    # chop off the final .\r\n
        return terminate, s

    def init_handler(self,msg,rtype):
        reply = self.SYN_ERR
        if rtype == RequestType.HELO:
            reply = self.HELO
        elif rtype == RequestType.FROM:
            source = MailAddress(msg)
            if source.valid:
                self.df = MailDataFrame(source)
                self.state = ServerState.RCPT
                reply = self.OK
        elif rtype in self.rtypes.values():
            reply = self.SEQ_ERR
        return reply

    def rcpt_handler(self,msg,rtype):
        reply = self.SYN_ERR
        if rtype == RequestType.RCPT:
            rcpt = MailAddress(msg)
            if rcpt.valid:
                if rcpt.domain in self.domains:
                    self.df.add_rcpt(rcpt)
                    reply = self.OK
                else:
                    reply = self.DOM_ERR
        elif rtype == RequestType.DATA:
            if len(self.df.rcpts) < 1:
                reply = self.NO_RCPT
            else:
                reply = self.DATA
                self.state = ServerState.DATA
        elif rtype in self.rtypes.values():
            reply = self.SEQ_ERR
        return reply

    def data_handler(self,msg,rtype):
        reply = self.SYN_ERR
        self.df.add_data(msg)
        if rtype == RequestType.LINE:
            self.noreply = True
        elif rtype == RequestType.TERM:
            self.noreply = False
            self.q.put(self.df)
            self.state = ServerState.INIT
            reply = self.OK + "; Queue indexing not supported"
        return reply


