# Assignment 4: Object Oriented Programming for a Timer
# Authors: Willow Woon, Matthew Pohl

from machine import Pin, I2C
import time
import i2c_lcd
from rotary_irq import RotaryIRQ

# Using a package from Mike Teachman (2021)
# For the HW - 040 Rotary Encoder
# https://opensource.org/licenses/MIT

# Rotary Encoder (Transmitting Data)
class RotIRQ:
    def __init__(self, clk=13, dt=14):
            self.encoder = RotaryIRQ(pin_num_clk=clk, 
                                 pin_num_dt=dt, 
                                 min_val=0,            # minimum 0 seconds into a minute
                                 max_val=60,           # maximum 60 seconds into a minute
                                 reverse=False,        # increase with counter-clockwise rotation
                                 range_mode=RotaryIRQ.RANGE_WRAP)

    def value(self):
        return self.encoder.value()

# Display (Recieving Data and Displaying it to the User Visually)
class Display:
    def __init__(self, scl=22, sda=23, addr=0x27):
        self.i2c = I2C(0, scl=Pin(scl), sda=Pin(sda))
        self.lcd = i2c_lcd.I2cLcd(self.i2c, addr, 2, 16)

    def update_screen(self, mins, secs, minMode):
        self.lcd.clear()
        label = "Set Mins" if minMode else "Set Secs"
        self.lcd.putstr(f"{label}:{mins:02d}:{secs:02d}")

    def show_countdown(self, m, s):
        self.lcd.clear()
        self.lcd.putstr(f"T-Minus:{m:02d}:{s:02d}")

    def times_up(self):
        self.lcd.clear()
        self.lcd.putstr("TIME'S UP!")
        
    def reset_screen(self):
        self.lcd.clear()
        self.lcd.putstr("RESET TIMER")

# Buzzer (Recieving Data and Notifying the User Audibly)
class Buzzer:
    def __init__(self, pin=19):
        self.pin = Pin(pin, Pin.OUT, value=1)

    def buzz(self, startButton, resetButton):
        if resetButton.value() == 1:
            for i in range(100):
                self.pin.value(1)
                time.sleep_ms(100)
                self.pin.value(0)
                time.sleep_ms(100)

                if startButton.value() == 0 or resetButton.value() == 0:
                    self.pin.value(1)
                    break
                
# Controls (Transmitting Data)
## BRAINS OF THE OPERATION ##
class TimerController:
    
    # timer data (reading and writing variables; child class of TimerController)
    class TimerData: 
        def __init__(self):
            self.mins = 0
            self.secs = 0
            self.minMode = True # minMode = True so minutes will be changed first
        
        def total_seconds(self):
            return (self.mins * 60) + self.secs
        
        def reset(self):
            self.mins = 0
            self.secs = 0
            self.minMode = True
    
    def __init__(self):      
        self.display = Display()
        self.buzzer = Buzzer()
        self.timer = self.TimerData()
        self.rotencoder = RotIRQ()

        self.startButton = Pin(12, Pin.IN, Pin.PULL_UP)
        self.modeButton = Pin(4, Pin.IN, Pin.PULL_UP)
        self.resetButton = Pin(15, Pin.IN)

        self.old_val = self.rotencoder.value()

    ## THIS FUNCTION RUNS THE WHOLE PROGRAM ##
    ## OTHER FUNCTIONS ARE THIS FUNCTION'S MINIONS :P ##
    ## THIS IS THE PREFRONTAL CORTEX ##
    def Run(self):
        self.display.update_screen(self.timer.mins, self.timer.secs, self.timer.minMode)
        
        while True:
            self.CheckRotary()
            self.CheckMode()
            if self.startButton.value() == 0:
                self.Countdown()
                
    # check if we are changing #secs or #mins
    def CheckMode(self):
        if self.modeButton.value() == 0:
            self.timer.minMode = not self.timer.minMode
            
            self.display.update_screen(self.timer.mins, self.timer.secs, self.timer.minMode)
            time.sleep(0.3)
    
    # update the value of the rotary encoder
    def CheckRotary(self):
        new_val = self.rotencoder.value()
        
        if self.old_val != new_val:
            if self.timer.minMode:
                self.timer.mins = new_val
            else:
                self.timer.secs = new_val
                
            self.old_val = new_val
            
            self.display.update_screen(self.timer.mins, self.timer.secs, self.timer.minMode)

    # countdown from total_seconds to zero
    def Countdown(self):
        total = self.timer.total_seconds() # calculate total_seconds
        
        for remaining in range(total, -1, -1):
            
            if self.resetButton.value() == 0: # cancel timer
                self.display.reset_screen()
                time.sleep(1)
                break
                
            m, s = divmod(remaining, 60) # div = mins, mod = secs
            self.display.show_countdown(m, s)
            
            if remaining == 0: # total_seconds has elapsed
                self.display.times_up()
                self.buzzer.buzz(self.startButton, self.resetButton)
            time.sleep(1)
        
        self.timer.reset()
        self.display.update_screen(0, 0, True)

# Initiate Program
brains = TimerController() # defining the brains as the TimeController class
brains.Run() # let the brains run the operation!
