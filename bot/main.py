#!/usr/bin/python

import sys
import os
import cv2
import numpy as np
import math
import threading
from time import sleep
import modules.Camera as Camera
import modules.Turret as Turret
import modules.Speak as Speak
import modules.Controller as Controller
from configobj import ConfigObj
 
# ===========================================================================
# This is the main executable for the robot.
# ===========================================================================

#load config
cfg = ConfigObj('/home/pi/bot/config.ini')

class ColorRange() :  
    def __init__(self):
        global cfg     
        self.hsvtolerance = [float(cfg['colortrack']['tolerance']['hue']),
                             float(cfg['colortrack']['tolerance']['saturation']),
                             float(cfg['colortrack']['tolerance']['value'])] 
    def setColorRange(self, hsvtarget):
        self.hsvlower = np.array([max(0,hsvtarget[0] - self.hsvtolerance[0]), 
                                  max(0,hsvtarget[1] - self.hsvtolerance[1]), 
                                  max(0,hsvtarget[2] - self.hsvtolerance[2])], dtype=np.uint8)
        self.hsvupper = np.array([min(180,hsvtarget[0] + self.hsvtolerance[1]), 
                                  min(255,hsvtarget[1] + self.hsvtolerance[1]), 
                                  min(255,hsvtarget[2] + self.hsvtolerance[2])], dtype=np.uint8)

def getBestContour(imgmask, threshold):
    contours,hierarchy = cv2.findContours(imgmask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    best_area = threshold
    best_cnt = None
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > best_area:
            best_area = area
            best_cnt = cnt            
    return best_cnt


def on_click(event, cx, cy, flag, param):
    if(event==cv2.cv.CV_EVENT_LBUTTONDOWN):
        print "moving..." + str(cx),str(cy)
        coords = (cx,cy)
        newturr = turret.coordToPulse(coords)
        currturr = (turret.xy[0],turret.xy[1])
        turret.sendTarget(newturr, currturr)   
    if(event==cv2.cv.CV_EVENT_MBUTTONDOWN):
        print "firing..."
        turret.fire()
    if(event==cv2.cv.CV_EVENT_RBUTTONDOWN):
        print "exiting...(to do)"

     
def main() :
     
    global cam, turret
    
    #start cam
    cam = Camera.Capture(cfg)    
    cam.getFrame() #need frame during init
    
    #start turret
    turret = Turret.Targetting(cfg)
    turret.daemon = True
    turret.recenter()
    turret.start()
    
    #start controller
    cmdlistener = Controller.Listener(cfg)
    cmdlistener.startlisteners()
    key = ""
    
    #facetrack
    modeface = False
    faceCascade = None
    #colortrack
    hsv = ColorRange()   
    areathreshold = int(cfg['colortrack']['areathreshold']) / cam.scaledown 
    sampleradius = int(cfg['colortrack']['sampleradius']) / int(cam.scaledown) 
    adjustpercent = float(cfg['colortrack']['adjustpercent'])
    hsvtarget = None #HSV range: 0-180,255,255   
    bgrtarget = None #for display only    
    #motion detect
    avgframe = np.float32(cam.frame)
    avgtimer = threading.Event()
    modemotion = False
    motionstarted = False
    
    #other
    t = None
    fps = None
    
    #display
    if os.environ.get('DISPLAY') and int(cfg['camera']['display']):
        display = True
        print 'display found'
    else:
        display = False
        print 'no display'
    if display:
        cv2.namedWindow("display", cv2.cv.CV_WINDOW_NORMAL)
        cv2.setMouseCallback("display", on_click, 0)
    
    #speak
    speak = Speak.Speak(cfg)
    speak.say("ready")
    
    while(1):
        
        #capture frame,position
        framexy = turret.xy
        cam.getFrame()        
        if display: #default display
            displayframe = cam.frame
                                
        #track target - hsv target set
        if not hsvtarget == None:
            #find best contour in hsv range
            framehsv = cv2.cvtColor(cam.frame, cv2.COLOR_BGR2HSV)
            framemask = cv2.inRange(framehsv, hsv.hsvlower, hsv.hsvupper) 
            if display: #color copy
                displaymaskframe = cv2.cvtColor(framemask.copy(), cv2.COLOR_GRAY2BGR)
                displayframe = cv2.addWeighted(cam.frame, 0.7, displaymaskframe, 0.3, 0)
            best_cnt = getBestContour(framemask, areathreshold)  
            if not best_cnt == None: #if match found
                #get center
                M = cv2.moments(best_cnt)
                cx,cy = int(M['m10']/M['m00']), int(M['m01']/M['m00'])                    
                #update turret
                turret.sendTarget(turret.coordToPulse((cx,cy)), framexy)
                if display:
                    #display circle target
                    objcenter = (cx,cy)
                    objradius = int(round(math.sqrt(cv2.contourArea(best_cnt)),2))
                    cv2.circle(displayframe, objcenter, objradius, (0,0,0), 5)
                    cv2.circle(displayframe, objcenter, objradius, bgrtarget, 3)
        #find a target
        else: 
            if modemotion == True: 
                if avgtimer.isSet():
                    cv2.accumulateWeighted(cam.frame, avgframe, 0.8) 
                    resframe = cv2.convertScaleAbs(avgframe)
                else:   
                    if not motionstarted:
                        speak.say("watching")
                        motionstarted = True 
                    #mask all motion  
                    motionmask = cv2.absdiff(cam.frame, resframe)
                    motionmask = cv2.cvtColor(motionmask, cv2.COLOR_RGB2GRAY)
                    _,motionmask = cv2.threshold(motionmask, 25, 255, cv2.THRESH_BINARY)
                    if display:
                        displayframe = motionmask.copy()
                    #find best
                    cntmask = motionmask.copy()
                    cnt = getBestContour(cntmask, areathreshold)               
                    if not cnt == None:
                        #motion found - mask best, get mean
                        cv2.rectangle(motionmask, tuple([0,0]), tuple([cam.w,cam.h]), (0,0,0), -1) 
                        cv2.drawContours(motionmask, tuple([cnt]), 0, (255,255,255), -1)
                        bgrtarget = cv2.mean(cam.frame, motionmask)
                        framehsv = cv2.cvtColor(cam.frame, cv2.COLOR_BGR2HSV)
                        hsvtarget = cv2.mean(framehsv, motionmask)
                        #set target
                        speak.say("Targetting " + Speak.BGRname(bgrtarget))
                        turret.armed = True
                        hsv.setColorRange(hsvtarget)
                        modemotion = False
            # Detect faces in the image            
            if modeface == True:
                gray = cv2.cvtColor(cam.frame, cv2.COLOR_BGR2GRAY)
                faces = faceCascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags = cv2.cv.CV_HAAR_SCALE_IMAGE
                )
                # closest face
                best_area = 0
                best_rect = None
                for (x, y, w, h) in faces:
                    area = w*h
                    if area > best_area:
                        best_area = area
                        best_rect = (x, y, w, h)
                
                #if face, go for shirt color
                if not best_rect == None:
                    xs = int(x + (x/2)) #shirt
                    ys = int(y+(h*1.7)) #shirt                
                    framecenter = cam.frame[ys-sampleradius:ys+sampleradius, xs-sampleradius:xs+sampleradius]
                    framecenterhsv = cv2.cvtColor(framecenter, cv2.COLOR_BGR2HSV)
                    hsvtarget = [int(cv2.mean(framecenterhsv)[0]), int(cv2.mean(framecenterhsv)[1]), int(cv2.mean(framecenterhsv)[2])]
                    bgrtarget = [int(cv2.mean(framecenter)[0]), int(cv2.mean(framecenter)[1]), int(cv2.mean(framecenter)[2])]
                    speak.say("Hey, you in the " + Speak.BGRname(bgrtarget) + " shirt")
                    hsv.setColorRange(hsvtarget)
                    modeface = False                
    #            if display:
    #                displayframe = gray.copy()            
    #                if not best_rect == None:
    #                    cv2.rectangle(displayframe, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
        if display:
            cv2.imshow('display', displayframe)
            cv2.waitKey(1)
        
        #print fps                
        if fps > 0:
            print str(cv2.getTickFrequency() / (cv2.getTickCount() - t))
            t = cv2.getTickCount()
            fps = fps - 1
            
        #command handler
        if cmdlistener.cmdsent.isSet():
            key = cmdlistener.cmd   
            cmdlistener.reset()  
            if key=="q": #quit
                speak.say("bye")
                turret.quit()
                cam.quit()
                cmdlistener.quit()
                cfg.write()
                if display:
                    cv2.destroyAllWindows()
                break
            elif key==" ": #reset all
                speak.say("Reset")
                hsvtarget = None
                turret.armed = False
                modemotion = False
                motionstarted = False
                modeface = False
                turret.recenter()       
            if key=="j": #joke/taunt
                speak.taunt()
            if key=="t": #test fire
                turret.fire()
            if key=="p": #toggle armed
                turret.armed = not turret.armed
                if turret.armed:
                    speak.say("armed")
                else:
                    speak.say("disarmed")   
            if key=="n": #toggle noisy
                if speak.quiet:
                    speak.quiet = 0
                    speak.say("talking")
                else:
                    speak.say("quiet")
                    sleep(.1) 
                    speak.quiet = 1
                cfg['speak']['quiet'] = speak.quiet
            elif key=="+": #volume
                speak.volume(.1)
                speak.say("check")
            elif key=="-": #volume
                speak.volume(-.1)
                speak.say("check")
            elif key=="y": #restart speak
                speak = Speak.Speak()
                speak.say("ok")
            elif key=="?": #fps
                fps = 20
                t = cv2.getTickCount() 
            elif key=="1": #start motion detect
                speak.say("Preparing motion detection.")
                modemotion = True
                motionstarted = False
                Timer.Countdown(5, avgtimer).thread.start()
                sleep(.1) #timer set
            elif key=="3": #start face detect
                speak.say("Seeking humans.")
                modeface = True
                faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
            elif key=="2": #sample center of image          
                framecenter = cam.frame[(cam.h/2)-sampleradius:(cam.h/2)+sampleradius, (cam.w/2)-sampleradius:(cam.w/2)+sampleradius]
                framecenterhsv = cv2.cvtColor(framecenter, cv2.COLOR_BGR2HSV)
                hsvtarget = [int(cv2.mean(framecenterhsv)[0]), int(cv2.mean(framecenterhsv)[1]), int(cv2.mean(framecenterhsv)[2])]
                bgrtarget = [int(cv2.mean(framecenter)[0]), int(cv2.mean(framecenter)[1]), int(cv2.mean(framecenter)[2])]
                speak.say("Targetting " + Speak.BGRname(bgrtarget))
                hsv.setColorRange(hsvtarget)
            else: #manual adjustments
                # l/m = +/- target sensitivity                       
                if key=="l":
                    turret.firesensitivity = turret.firesensitivity * (1+adjustpercent)
                if key=="m":
                    turret.firesensitivity = turret.firesensitivity * (1-adjustpercent)
                # a,s,d/z,x,c = +/- H,S,V
                if key=="a": hsv.hsvtolerance[0] = hsv.hsvtolerance[0] * (1+adjustpercent)
                if key=="z":
                    hsv.hsvtolerance[0] = hsv.hsvtolerance[0] * (1-adjustpercent)
                if key=="s": #sat
                    hsv.hsvtolerance[1] = hsv.hsvtolerance[1] * (1+adjustpercent)
                if key=="x":
                    hsv.hsvtolerance[1] = hsv.hsvtolerance[1] * (1-adjustpercent)
                if key=="d": #val
                    hsv.hsvtolerance[2] = hsv.hsvtolerance[2] * (1+adjustpercent)
                if key=="c":
                    hsv.hsvtolerance[2] = hsv.hsvtolerance[2] * (1-adjustpercent)
                # f/v = +/- threshhold area
                if key=="f": #area
                    areathreshold = areathreshold * (1+adjustpercent)
                if key=="v":
                    areathreshold = areathreshold * (1-adjustpercent)           
                #adjust target settings/range
                if not hsvtarget == None:
                    hsv.setColorRange(hsvtarget)
                    print ">> HSV:", hsvtarget[0], hsvtarget[1], hsvtarget[2], "Range:", hsv.hsvtolerance[0], hsv.hsvtolerance[1], hsv.hsvtolerance[2], "Area:", areathreshold, "Armed:", turret.armed,turret.firesensitivity
                    
        
if __name__ == "__main__" :
    #start
    sys.exit(main())
    
