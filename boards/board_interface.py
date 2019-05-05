NOT_IMPLEMENTED = "NOT IMPLEMENTED"

class BoardInterface(object):
    def __init__(self, bname, bport, num_channels):
        self.name = bname
        self.port = bport
        self.num_channels = num_channels
        self.current_status = 0x00


    def getCurrentStatus (self):
        return NOT_IMPLEMENTED

    def setRelay (self, new_status, channel):
        return NOT_IMPLEMENTED

    def getRelay (self, channel):
        return NOT_IMPLEMENTED

    def ModelName (self):
        return NOT_IMPLEMENTED