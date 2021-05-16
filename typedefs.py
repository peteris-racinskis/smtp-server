import re
from enum import Enum


class MailAddress():

    def __init__(self, s):
        self.valid = False
        self.parse_address(s)

    def parse_address(self, s):
        # < ... >               <- between <> brackets
        # ([a-z]+)              <- 1..inf lowercase letters
        # @                     <- literal
        # ([a-z]+\.[a-z]{1,3})  <- domain.com
        pattern = re.compile(r'<([a-z]+)@([a-z]+\.[a-z]{1,3})>')
        m = re.search(pattern, s)
        if m:
            self.user     = m.group(1)
            self.domain   = m.group(2)
            self.literal  = self.user + "@" + self.domain
            self.valid    = True


class ServerState(Enum):
    INIT = 0
    RCPT = 1
    DATA = 2
    QUIT = 3

class RequestType(Enum):
    HELO = 0
    FROM = 1    # MAIL FROM
    RCPT = 2    # RCPT TO
    DATA = 3
    QUIT = 4    
    FAIL = 5    # Bad request
    RSET = 6    # Clear buffers, return to init
    TERM = 7    # Terminate data block
    LINE = 8    # Data line


class MailDataFrame():

    def __init__(self,source):
        self.source = source
        self.rcpts = []
        self.data  = []
    
    def add_rcpt(self,rcpt):
        self.rcpts.append(rcpt)

    def add_data(self,data):
        self.data.append(data)