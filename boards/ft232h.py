# Import GPIO and FT232H modules.
import sys
print (sys.path)
from Adafruit_GPIO import GPIO
import Adafruit_GPIO.FT232H as FT232H

from .board_interface import BoardInterface, NOT_IMPLEMENTED

model_name = "ada_ft232h"

class ada_ft232h(BoardInterface):
    def __init__(self, bname, bport, num_channels):
        super(ada_ft232h,self).__init__(bname, bport, num_channels)
        # Temporarily disable the built-in FTDI serial driver on Mac & Linux platforms.
        FT232H.use_FT232H()

        # Create an FT232H object that grabs the first available FT232H device found.
        self.ft232h = FT232H.FT232H()

        # Configure digital inputs and outputs using the setup function.
        # Note that pin numbers 0 to 15 map to pins D0 to D7 then C0 to C7 on the board.
        #ft232h.setup(7, GPIO.IN)   # Make pin D7 a digital input.
        for pin in range(0,16):
            self.ft232h.setup(pin, GPIO.OUT)  # Make pin C0 a digital output.

        self.getCurrentStatus();


    def getCurrentStatus (self):
        self.current_status = self.ft232h.mpsse_read_gpio()
        return self.current_status

    def setRelay (self, new_status, channel):
        self.ft232h.output(channel, not new_status)
        return NOT_IMPLEMENTED

    def getRelay (self, channel):
        self.getCurrentStatus();
        return (1 << channel) & self.current_status

    @staticmethod
    def ModelName ():
        return model_name
