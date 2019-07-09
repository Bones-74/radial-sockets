NOT_IMPLEMENTED = "NOT IMPLEMENTED"

class BoardInterface(object):
    ALL_OK = 0
    CHANNEL_ALREADY_ASSIGNED = -1

    CHANNEL_INPUT = 1
    CHANNEL_OUTPUT = 0

    ACTIVE_LOW = 0
    ACTIVE_HIGH = 0

    def __init__(self, bname, bport, num_channels):
        self.name = bname
        self.port = bport
        self.num_channels = num_channels
        self.current_status = 0x00

    def addChannel(self, channel, sense, direction):
        return NOT_IMPLEMENTED

    def configure(self):
        return NOT_IMPLEMENTED

    def getCurrentStatus (self):
        return NOT_IMPLEMENTED

    def setRelay (self, new_status, channel):
        return NOT_IMPLEMENTED

    def getRelay (self, channel):
        return NOT_IMPLEMENTED

    def ModelName (self):
        return NOT_IMPLEMENTED