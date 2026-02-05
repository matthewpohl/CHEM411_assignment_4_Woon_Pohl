# setup
from machine import Pin, I2C, ADC
import machine as m
from rotary import Rotary
from sys import platform
import time
import i2c_lcd


# Using a package from Mike Teachman (2021)
# For the HW - 040 Rotary Encoder
# https://opensource.org/licenses/MIT

import sys
if sys.platform == 'esp8266' or sys.platform == 'esp32':
    from rotary_irq import RotaryIRQ
elif sys.platform == 'pyboard':
    from rotary_irq_pyb import RotaryIRQ
elif sys.platform == 'rp2':
    from rotary_irq_rp2 import RotaryIRQ
else:
    print('Warning:  The Rotary module has not been tested on this platform')

## setup

# rotary encoder setup
r = RotaryIRQ(pin_num_clk=13, # CLK (Input)
              pin_num_dt=14,  # DT (Input)
              min_val=0,
              max_val=60,
              reverse=False,
              range_mode=RotaryIRQ.RANGE_WRAP)

# rotary encoder push-button
R = Pin(15, Pin.IN) # SW (Input)

# setup I2C LCD
screen = I2C(0, scl=Pin(22), sda=Pin(23))
lcd = i2c_lcd.I2cLcd(screen, 0x27, 2, 16)

# setup buttons and buzzer
MinSec = Pin(4, Pin.IN, Pin.PULL_UP)
Start = Pin(12, Pin.IN, Pin.PULL_UP)
buzzer = m.Pin(19, m.Pin.OUT) 

# variables
mins = 0
secs = 0
MinMode = True # boolean variable (mins setting or secs setting)
OldVal = r.value() # define OldVal for rotary encoder
buzzer.value(1)

#class Feedback():
#class Model():

#class Controller():
#class View():
def UpdateScreen(mins, secs):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("M:%02d S:%02d    " % (mins, secs))
    lcd.move_to(0, 1)

def CountDown(TotSec):
    while TotSec > 0:
        m, s = divmod(TotSec, 60)
        lcd.clear()
        lcd.putstr("Time: {:02d}:{:02d}".format(m, s))
            
        time.sleep(1)
        TotSec -= 1
        if R.value() == 0:
            break

def Buzz():
    lcd.clear()
    lcd.putstr("TIME'S UP!")
    
    if R.value() == 1: # if - else statement to prevent unessecary beeping upon reset
        for i in range(100):
            buzzer.value(1)
            time.sleep_ms(100)
            buzzer.value(0)
            time.sleep_ms(100)
            if Start.value() == 0 or R.value() == 0:
                return
    else:
        return
        
def Reset():
    buzzer.value(1)

    mins = 0
    secs = 0
    MinMode = True # Tracks if we are setting Minutes or Seconds
    UpdateScreen(mins, secs)
    TotSec = 0
    r.value()
    
def CountDown(TotSec):
    while TotSec > 0:
        secs = TotSec % (24 * 3600)
        secs %= 3600
        mins = TotSec // 60
        secs %= 60
        UpdateScreen(mins, secs)
        time.sleep(1)
        TotSec -= 1
        if R.value() == 0:
            break
                
UpdateScreen(mins, secs)

while True:
    
    # toggle between mins and secs
    if MinSec.value() == 0:
        MinMode = not MinMode # flip the boolean
        time.sleep(0.2) # Debounce delay to prevent multiple toggles
    
    # read the rotary encoder
    NewVal = r.value()
    
    # change the minutes
    if MinMode and OldVal != NewVal:
        OldVal = NewVal
        mins = NewVal
        UpdateScreen(mins, secs)
        time.sleep_ms(10)
        
        if R.value() == 0:
            Reset()
    
    # change the seconds
    if not MinMode and OldVal != NewVal:
        OldVal = NewVal
        secs = NewVal
        UpdateScreen(mins, secs)
        time.sleep_ms(10)
        
        if R.value() == 0:
            Reset()
    
    # check if start button is pressed
    if Start.value() == 0:
        TotSecs = (mins * 60) + secs
        CountDown(TotSecs)
        Buzz()
        Reset()
        
    # reset the program
    if R.value() == 0:
        Reset()

    time.sleep_ms(50)
