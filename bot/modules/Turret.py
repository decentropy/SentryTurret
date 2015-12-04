#!/usr/bin/python

from driver.Adafruit_PWM_Servo_Driver import PWM
import threading
from time import sleep

# ===========================================================================
# Wrapper for your servo driver goes here.
# move() is called with servo positions in range -1(left/down)...0(center)...1(right/up)
#
# This example implements Adafruit PWM servo driver from RaspberryPi
# https://learn.adafruit.com/adafruit-16-channel-servo-driver-with-raspberry-pi
# ===========================================================================
class ServoDriver :

    def __init__(self, cfg):
        # PWM settings
        FREQ = 60.0  # Set frequency to 60 Hz  
        self.pwm = PWM(0x40, debug=False)      
        self.pwm.setPWMFreq(FREQ)
        pulseLength = 1000000                   # 1,000,000 us per second
        pulseLength /= FREQ                       # 60 Hz
        pulseLength /= 4096                     # 12 bits of resolution
        self.pulseFactor = 1000 / pulseLength	# millisecond multiplier
        # Tested Servo range
        self.pulsecenter = float(cfg['turret']['pulsecenter'])
        self.pulserange = float(cfg['turret']['pulserange'])

    def move(self, servo, position):  
        if -1 < position < 1:   #movement range -1...0...1
            pulse = self.pulsecenter + (position*self.pulserange) 	# w/in range from middle
            pulse *= self.pulseFactor		# ~120-600 at 60hz
            self.pwm.setPWM(servo, 0, int(pulse))


class Countdown(threading.Thread):
    def __init__(self, seconds, event):
        self.runTime = seconds
        self.event = event
        self.thread = threading.Thread(target=self.run)
    def run(self):
        if not self.event.isSet():
            self.event.set()
            sleep(self.runTime)
            self.event.clear()

            
#globals
threadquit = threading.Event()


class Targetting(threading.Thread) : 
  
    def __init__(self, cfg):
    
        #settings
        self.servoX = int(cfg['turret']['panchannel'])
        self.servoY = int(cfg['turret']['tiltchannel'])
        self.servoF = int(cfg['turret']['triggerchannel'])
        self.center = [float(cfg['turret']['centerx']), float(cfg['turret']['centery'])] 
        self.fps = int(cfg['camera']['fps'])
        self.stepsleep = float(cfg['turret']['stepsleep'])
        self.firesensitivity = float(cfg['turret']['firesensitivity'])
        self.triggerwait = float(cfg['turret']['reloadseconds'])
        self.pixelPulseRatio = float(cfg['turret']['pixelsperpulse'])
        self.camW = int(cfg['camera']['width'])
        self.camH = int(cfg['camera']['height'])
        self.driver = ServoDriver(cfg)
        self.cfg = cfg
        
        self.wmiddle = self.camW/2
        self.hmiddle = self.camH/2
        self.triggertimer = threading.Event()
        self.armed = False
        self.xy = self.center[:]  #current xy
        self.deltaxy = [0.0, 0.0]  #current move
        self.deltaxylast = [0.0, 0.0]  #prior move
        self.stepxy = [0.0, 0.0]  #xy per step
        self.steps = (1.0/self.fps)/self.stepsleep #steps per frame
        self.stepcounter = 0 #motion step counter
        threading.Thread.__init__(self)
        
    def coordToPulse(self, coord):
        xpulse = (float(coord[0]) - self.wmiddle) / self.pixelPulseRatio
        ypulse = (self.hmiddle - float(coord[1])) / self.pixelPulseRatio
        return (xpulse,ypulse)
        
    def fire(self): #pull trigger
        #CUSTOMIZE THIS, per your servo configuration
        self.driver.move(self.servoF, 0 )
        sleep(.2) #todo: should be calculated
        self.driver.move(self.servoF, float(self.cfg['turret']['fireposition']) )
        sleep(.2) #todo: should be calculated
        self.driver.move(self.servoF, 0 )
        Countdown(self.triggerwait, self.triggertimer).thread.start()  #between fire
        
    def recenter(self):
        #zero to center
        self.stepcounter = 0
        self.sendTarget([-self.xy[0]+self.center[0], -self.xy[1]+self.center[1]], self.xy)
        
    def sendTarget(self, pulsexy, framexy): #pulsexy: delta from 0,0 / framexy: position at capture
        self.deltaxylast = self.deltaxy[:]
        #subtract distance since capture
        self.deltaxy[0] = pulsexy[0]-(self.xy[0]-framexy[0])
        self.deltaxy[1] = pulsexy[1]-(self.xy[1]-framexy[1])
        #stay on newest delta
        if self.stepcounter > 0:
            if abs(self.deltaxy[0])<abs(self.deltaxylast[0]):
                self.stepxy[0] = 0.0
            if abs(self.deltaxy[1])<abs(self.deltaxylast[1]):
                self.stepxy[1] = 0.0
        '''
        if abs(self.deltaxy[0])<abs(self.deltaxylast[0]) or abs(self.deltaxy[1])<abs(self.deltaxylast[1]):
            self.stepcounter = 0
        '''
        #fire if on target
        if self.armed and not self.triggertimer.isSet():
            if (-(self.firesensitivity) < self.deltaxy[0] < self.firesensitivity) and (-(self.firesensitivity) < self.deltaxy[1] < self.firesensitivity):
                print ">>> PEW! PEW!"
                if not self.deltaxy[0] == 0:
                    self.fire()
                    
    def quit(self): #cleanup
        global threadquit
        self.recenter()
        sleep(1)
        threadquit.set()
        
    def run(self):
        global threadquit
        while(not threadquit.isSet()):
            sleep(self.stepsleep)
            if self.stepcounter>0: #stepping to target
                self.xy[0] += self.stepxy[0]
                self.driver.move(self.servoX, self.xy[0] )
                self.xy[1] += self.stepxy[1]
                self.driver.move(self.servoY, self.xy[1] )
                self.stepcounter -= 1
            else: #set next target
                self.stepxy[0] = self.deltaxy[0]/self.steps 
                self.stepxy[1] = self.deltaxy[1]/self.steps 
                self.deltaxy = [0.0, 0.0]
                self.stepcounter = self.steps
                
