from .board_interface import BoardInterface, NOT_IMPLEMENTED

model_name = "B01"

class B01(BoardInterface):
    def __init__(self, bname, bport, num_channels):
        super(B01,self).__init__(bname, bport, num_channels)

    def getCurrentStatus (self):
        return NOT_IMPLEMENTED

    def setRelay (self, new_status, channel):
        return NOT_IMPLEMENTED

    def getRelay (self, channel):
        return NOT_IMPLEMENTED

    @staticmethod
    def ModelName ():
        return model_name