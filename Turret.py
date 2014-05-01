#!/usr/bin/python

import driver.MyDriverWrapper 
import threading
import Timer
from time import sleep
        
#globals
threadquit = threading.Event()

class Controller(threading.Thread) : 
  
    def __init__(self):
        # My Servo pins
        self.servoX = 15 #pan servo
        self.servoY = 3 #tilt servo
        self.servoF = 1 #trigger servo
        self.driver = driver.MyDriverWrapper.ServoDriver()
        #=========== 
        self.center = [0.0, -0.2] #where to recenter
        self.fps = 1.5 #frame per seconds  *** movement is wild if set too high ***
        self.stepsleep = 0.05 #time per step (smoothness)
        self.firesensitivity = .02 #how trigger happy
        self.triggerwait = 3 #seconds between fire/reload
        #variables
        self.triggertimer = threading.Event()
        self.armed = False #will fire
        self.xy = self.center[:]  #current xy
        self.deltaxy = [0.0, 0.0]  #current move
        self.deltaxylast = [0.0, 0.0]  #prior move
        self.stepxy = [0.0, 0.0]  #xy per step
        self.steps = (1.0/self.fps)/self.stepsleep #steps per frame
        self.stepcounter = 0 #motion step counter
        threading.Thread.__init__(self)
        
    def fire(self): #pull trigger
        self.driver.move(self.servoF, 0 )
        sleep(.2)            
        self.driver.move(self.servoF, 0.1 )
        sleep(.2)             
        self.driver.move(self.servoF, 0 )
        Timer.Countdown(self.triggerwait, self.triggertimer).thread.start()  #between fire
        
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
                
