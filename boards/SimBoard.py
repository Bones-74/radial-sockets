from .board_interface import BoardInterface

model_name = "SIM"

class SimBoard(BoardInterface):
    def __init__(self, bname, bport, num_channels):
        super(SimBoard,self).__init__(bname, bport, num_channels)

        self.channels = [0] * num_channels

    def getCurrentStatus (self):
        # pretend to get real info from relay board, ie, do nothing!
        return self.channels

    def setRelay (self, new_status, channel):
        self.channels[channel] = new_status
        return new_status

    def getRelay (self, channel):
        return self.channels[channel]

    @staticmethod
    def ModelName ():
        return model_name