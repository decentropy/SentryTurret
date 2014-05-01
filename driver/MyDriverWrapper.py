#!/usr/bin/python

from Adafruit_PWM_Servo_Driver import PWM

# ===========================================================================
# Wrapper for your servo driver goes here.
# move() is called with servo positions in range -1(left/down)...0(center)...1(right/up)
#
# This example implements Adafruit PWM servo driver from RaspberryPi
# https://learn.adafruit.com/adafruit-16-channel-servo-driver-with-raspberry-pi
# ===========================================================================

class ServoDriver :

    def __init__(self):
        # PWM settings
        FREQ = 60.0  # Set frequency to 60 Hz  
        self.pwm = PWM(0x40, debug=False)      
        self.pwm.setPWMFreq(FREQ)
        pulseLength = 1000000                   # 1,000,000 us per second
        pulseLength /= FREQ                       # 60 Hz
        pulseLength /= 4096                     # 12 bits of resolution
        self.pulseFactor = 1000 / pulseLength	# millisecond multiplier
        # Tested Servo range
        self.pulsecenter = 1.6
        self.pulserange = 0.8 #per adafruit 0.5 = 1.0...1.5...2.0

    def move(self, servo, position):        
        if -1 < position < 1:   #movement range -1...0...1
            pulse = self.pulsecenter + (position*self.pulserange) 	# w/in range from middle
            pulse *= self.pulseFactor		# ~120-600 at 60hz
            self.pwm.setPWM(servo, 0, int(pulse))
