# Import GPIO and FT232H modules.
import sys
print (sys.path)
from Adafruit_GPIO import GPIO
import Adafruit_GPIO.FT232H as FT232H

from .board_interface import BoardInterface, NOT_IMPLEMENTED

model_name = "ada_ft232h"

# pin d0-d7 channels 0-7
# pin c0-c7 channels 8-15

class ada_ft232h(BoardInterface):
    def __init__(self, bname, bport, num_channels):
        super(ada_ft232h,self).__init__(bname, bport, num_channels)

        #FT232H.enumerate_device_serials()

        # Temporarily disable the built-in FTDI serial driver on Mac & Linux platforms.
        FT232H.use_FT232H()

        # Create an FT232H object that grabs the first available FT232H device found.
        self.ft232h = FT232H.FT232H()

        self.channel_dirs = dict()
        self.channel_sense = dict()
        self.channel_configured = dict()

        # initialise all gpio as inputs first of all
        for pin in range(0,16):
            self.ft232h.setup(pin, GPIO.IN)  # Make pin a digital input


    def addChannel(self, gpio, direction):
        if gpio.channel in self.channel_dirs:
            return BoardInterface.CHANNEL_ALREADY_ASSIGNED

        self.channel_dirs [gpio.channel] = direction
        self.channel_sense [gpio.channel] = gpio.sense
        self.channel_configured [gpio.channel] = False

        return BoardInterface.ALL_OK

    def configure(self):
        # Configure digital inputs and outputs using the setup function.
        # Note that pin numbers 0 to 15 map to pins D0 to D7 then C0 to C7 on the board.
        #ft232h.setup(7, GPIO.IN)   # Make pin D7 a digital input.
        for pin in range(0,16):
            if pin in self.channel_dirs:
                if self.channel_dirs[pin] == BoardInterface.CHANNEL_OUTPUT:
                    self.ft232h.setup(pin, GPIO.OUT)  # Make pin C0 a digital output.
                else:
                    self.ft232h.setup(pin, GPIO.IN)  # Make pin C0 a digital output.

        self.getCurrentStatus();


    def getCurrentStatus (self):
        read_current_status = self.ft232h.mpsse_read_gpio()
        processed_current_status = 0
        for channel_num, _direction in self.channel_dirs.items():
            current_pin_value = (1 << channel_num) & read_current_status
            if self.channel_sense [channel_num] == BoardInterface.ACTIVE_LOW:
                # swap the bit so that it is represented by ACTIVE HIGH
                if not current_pin_value:
                    # currently '0' (representing active)- need to set bit
                    processed_current_status |= (1 << channel_num)
            else:
                processed_current_status |= (1 << channel_num)

        self.current_status = processed_current_status
        return self.current_status

    def setRelay (self, new_status, channel):
        if channel in self.channel_sense:
            if self.channel_sense [channel] == BoardInterface.ACTIVE_LOW:
                # Need to invert status
                new_status = not new_status

        self.ft232h.output(channel, new_status)

        # Only configure outputs after teh first value has been received to prevent
        # relay from being flipped on then off during initialisation.
        if channel in self.channel_configured:
            if not self.channel_configured [channel]:
                if self.channel_dirs [channel] == BoardInterface.CHANNEL_OUTPUT:
                    self.ft232h.setup(channel, GPIO.OUT)  # Make pin C0 a digital output.

    def getRelay (self, channel):
        self.getCurrentStatus();
        current_pin_value = (1 << channel) & self.current_status

        return bool(current_pin_value)

    @staticmethod
    def ModelName ():
        return model_name
