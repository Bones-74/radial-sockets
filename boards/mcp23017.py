# Import GPIO and FT232H modules.
import sys
#print (sys.path)
import wiringpi as wiringpi

from .board_interface import BoardInterface, NOT_IMPLEMENTED
from numpy import int16

model_name = "mcp23017"

# pin a0-a7 channels 0-7
# pin b0-b7 channels 8-15

pin_base = 65       # lowest available starting number is 65

INPUT_PIN = 0
OUTPUT_PIN = 1

class mcp23017(BoardInterface):
    def __init__(self, bname, bport, num_channels):
        super(mcp23017,self).__init__(bname, bport, num_channels)

        # set the pin base for this i2c device, it doesn't matter which
        # mcp device get which set of pin numbers- it's all internal to
        # this driver.  externally, we use 0-15
        global pin_base
        self.pin_base = pin_base
        pin_base += 16

        # convert the 'port' to the device i2c address
        # port should be defined with leading '0x'
        i2c_addr = int(bport,0)

        # initialise wiringpi and setup mcpdriver for device
        wiringpi.wiringPiSetup()
        wiringpi.mcp23017Setup(self.pin_base, i2c_addr)


        self.channel_dirs = dict()
        self.channel_sense = dict()
        self.channel_configured = dict()

        # initialise all gpio as inputs first of all
        for pin in range(self.pin_base, 16):
            wiringpi.pinMode(pin, INPUT_PIN)


    def addChannel(self, gpio, direction):
        if gpio.channel in self.channel_dirs:
            return BoardInterface.CHANNEL_ALREADY_ASSIGNED

        self.channel_dirs [gpio.channel] = direction
        self.channel_sense [gpio.channel] = gpio.sense
        self.channel_configured [gpio.channel] = False

        return BoardInterface.ALL_OK

    def configure(self):
        return NOT_IMPLEMENTED

        # Configure digital inputs and outputs using the setup function.
        # Note that pin numbers 0 to 15 map to pins D0 to D7 then C0 to C7 on the board.
        #ft232h.setup(7, GPIO.IN)   # Make pin D7 a digital input.
        for pin in range(self.pin_base, 16):
            if pin in self.channel_dirs:
                if self.channel_dirs[pin] == BoardInterface.CHANNEL_OUTPUT:
                    self.ft232h.setup(pin, GPIO.OUT)  # Make pin C0 a digital output.
                else:
                    self.ft232h.setup(pin, GPIO.IN)  # Make pin C0 a digital output.

        self.getCurrentStatus();


    def getCurrentStatus (self):
        processed_current_status = 0
        for channel_num, _direction in self.channel_dirs.items():
            pin = self.pin_base + channel_num
            current_pin_value = wiringpi.digitalRead(pin)
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

        wiringpi.digitalWrite(self.pin_base + channel, new_status)

        # Only configure outputs after the first value has been received to prevent
        # relay from being flipped on then off during initialisation.
        if channel in self.channel_configured:
            if not self.channel_configured [channel]:
                if self.channel_dirs [channel] == BoardInterface.CHANNEL_OUTPUT:
                    self.channel_configured [channel] = True
                    wiringpi.pinMode(self.pin_base + channel, OUTPUT_PIN)

    def getRelay (self, channel):
        self.getCurrentStatus();
        current_pin_value = (1 << channel) & self.current_status

        return bool(current_pin_value)

    @staticmethod
    def ModelName ():
        return model_name
