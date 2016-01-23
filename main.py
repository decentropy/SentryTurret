#!/usr/bin/python

import sys
import os
import cv2
import dlib
import numpy as np
import threading
from time import sleep
import modules.Camera as Camera
import modules.Speak as Speak
import modules.Controller as Controller
import modules.Timer as Timer
import modules.Tracker as Tracker
import modules.Turret as Turret
    
 
# ===========================================================================
# This is the main executable for the robot.
# ===========================================================================


#if display, respond to mouse
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


#load config
from configobj import ConfigObj #this library supports writing/saving config
cfg = ConfigObj(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')

     
def main() :     
    global cam, turret
    
    #start cam
    cam = Camera.Capture(cfg)
    cam.daemon = True
    cam.start()
    i=0
    while (i<50): #allow 5sec for startup
        i += 1
        sleep(0.1)
        if cam.rawframe != None:
            break
    frame = cam.getFrame() #need during init
    
    #start turret
    turret = Turret.Targetting(cfg)
    turret.daemon = True
    turret.recenter()
    turret.start()
    
    #start controller
    cmdlistener = Controller.Listener(cfg)
    cmdlistener.startlisteners()
    key = ""
    
    #display
    displaytext = "" #for writing message in window
    if os.environ.get('DISPLAY') and int(cfg['camera']['display']):
        display = True
        print 'display found'
    else:
        display = False
        print 'no display'
    if display:
        cv2.namedWindow("display", cv2.cv.CV_WINDOW_AUTOSIZE)
        cv2.setMouseCallback("display", on_click, 0)
    
    #tracking functions
    track = Tracker.Tracking(cfg, display)
    tracker = None #dlib object tracking
    
    #motion detection
    avgframe = np.float32(frame)
    avgtimer = threading.Event() #TODO: put this in Timer thread?
    
    #speak
    speak = Speak.Speak(cfg)
    speak.say("ready")
    
    cam.resetFPS()
    
    while(1):
        
        #capture frame,position
        framexy = turret.xy
        frame = cam.getFrame()     
        if display: #default display
            displayframe = frame
            
        #targetting color (hsv)
        if track.mode == 4: 
            cx,cy,displayframe = track.targetHsv(frame)
            if cx:
                turret.sendTarget(turret.coordToPulse((cx,cy)), framexy)
        #targetting object (dlib) 
        if track.mode == 5: 
            tracker.update(frame)
            rect = tracker.get_position()
            cx = (rect.right() + rect.left()) / 2
            cy = (rect.top() + rect.bottom()) / 2
            turret.sendTarget(turret.coordToPulse((cx,cy)), framexy)
            if display:
                pt1 = (int(rect.left()), int(rect.top()))
                pt2 = (int(rect.right()), int(rect.bottom()))
                cv2.rectangle(displayframe, pt1, pt2, (255, 255, 255), 3)
        #detect motionhsv, motionobj
        elif track.mode == 2 or track.mode == 3: 
            if avgtimer.isSet():
                #learn image for motion detection
                cv2.accumulateWeighted(frame, avgframe, 0.8) 
                resframe = cv2.convertScaleAbs(avgframe)
            else:
                cnt, motionmask = track.getMotionContour(frame, resframe, track.areathresholdobject if track.mode==3 else track.areathresholdcolor)
                if display:
                    displayframe = cv2.cvtColor(motionmask.copy(), cv2.COLOR_GRAY2RGB)
                if not cnt == None:
                    #motionhsv
                    if track.mode == 2: #mask for mean
                        track.bgrtarget = cv2.mean(frame, motionmask)
                        framehsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                        track.hsvtarget = cv2.mean(framehsv, motionmask)
                        track.setColorRange()
                        turret.armed = True
                        displaytext = "Targetting " + Speak.BGRname(track.bgrtarget)
                        speak.say(displaytext)
                        track.mode = 4 #hsvtarget
                        cam.resetFPS()
                    #motionobj
                    if track.mode == 3: #object points
                        x,y,w,h = cv2.boundingRect(cnt)
                        if x>3 and y>3: # and x+w<cam.w-3 and y+h<cam.h-3: #object inside frame #TODO: which sides?
                            points = (x,y,x+w,y+h)
                            tracker = dlib.correlation_tracker()
                            tracker.start_track(frame, dlib.rectangle(*points))
                            displaytext = "Targetting object"
                            speak.say(displaytext)
                            track.mode = 5 #dlib
                            cam.resetFPS()
                        else:
                            cv2.rectangle(displayframe, (x, y), (x+w, y+h), (0,0,255), 2)
        #face        
        elif track.mode == 1:            
            detector = dlib.get_frontal_face_detector()
            faces = detector(frame)   
            best_area = 0
            best_face = None
            for d in faces:
                area = (d.left()-d.right())*(d.top()-d.bottom())
                if area > best_area:
                    best_area = area
                    best_face = d
            if not best_face == None: #face points
                points = (best_face.left(),best_face.top(),best_face.right(),best_face.bottom())
                tracker = dlib.correlation_tracker()
                tracker.start_track(frame, dlib.rectangle(*points))
                displaytext = "Targetting human"
                speak.say(displaytext)
                track.mode = 5 #dlib
                #if face, go for shirt color
#                xs = int(x + (x/2)) #shirt
#                ys = int(y+(h*1.7)) #shirt                
#                framecenter = frame[ys-track.sampleradius:ys+track.sampleradius, xs-track.sampleradius:xs+track.sampleradius]
#                framecenterhsv = cv2.cvtColor(framecenter, cv2.COLOR_BGR2HSV)
#                track.hsvtarget = [int(cv2.mean(framecenterhsv)[0]), int(cv2.mean(framecenterhsv)[1]), int(cv2.mean(framecenterhsv)[2])]
#                track.setColorRange()
#                track.bgrtarget = [int(cv2.mean(framecenter)[0]), int(cv2.mean(framecenter)[1]), int(cv2.mean(framecenter)[2])]
#                speak.say("Hey, you in the " + Speak.BGRname(track.bgrtarget) + " shirt")
#                track.mode = 4 #hsvtarget


        
        #display frame
        if display:
            if displaytext:
                textsize = 0.003 * cam.w
                cv2.putText(displayframe, displaytext, (5,cam.h-5), cv2.FONT_HERSHEY_SIMPLEX, textsize, (0,255,255))
            cv2.imshow('display', displayframe)
            cv2.waitKey(1)
            

# Command Handler --------------------------
        if cmdlistener.cmdsent.isSet():
            key = cmdlistener.cmd   
            cmdlistener.reset()  
            #quit/restart
            if key=="?" or key=="h":
                f = open(os.path.dirname(os.path.abspath(__file__)) + '/help.txt','r')
                print(f.read())
            elif key=="q" or key=="r": 
                turret.quit()
                cam.quit()
                cmdlistener.quit()
                cfg.write()
                if display:
                    cv2.destroyAllWindows()
                if key=="q":
                    speak.say("quitting. bye")
                    return 0
                if key=="r":
                    speak.say("restarting")
                    return 1
#--- Targeting ---            
            elif key==" ":  #reset all
                speak.say("Reset")
                displaytext = ""
                turret.armed = False
                track.mode = 0
                turret.recenter()  
                cam.resetFPS()   
            elif key=="t": #sample center of image
                sampleradius = 0.02 * (cam.w / float(cfg['camera']['scaledown']))
                framecenter = frame[(cam.h/2)-sampleradius:(cam.h/2)+sampleradius, (cam.w/2)-sampleradius:(cam.w/2)+sampleradius]
                framecenterhsv = cv2.cvtColor(framecenter, cv2.COLOR_BGR2HSV)
                track.hsvtarget = [int(cv2.mean(framecenterhsv)[0]), int(cv2.mean(framecenterhsv)[1]), int(cv2.mean(framecenterhsv)[2])]
                track.setColorRange()
                track.bgrtarget = [int(cv2.mean(framecenter)[0]), int(cv2.mean(framecenter)[1]), int(cv2.mean(framecenter)[2])]
                displaytext = "Targetting " + Speak.BGRname(track.bgrtarget)
                speak.say(displaytext)
                track.mode = 4
                cam.resetFPS()  
            elif key=="1": #start face detect
                displaytext = "Seeking humans."
                speak.say(displaytext)
                track.mode = 1 #face
                cam.resetFPS()
                #track.faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
            elif key=="2" or key=="3": #start motion detect: 2:hsv or 3:dlib
                displaytext = "Motion " + ("by color" if key=="2" else "by object")
                speak.say(displaytext)
                Timer.Countdown(5, avgtimer).thread.start()
                sleep(.1) #timer set
                track.mode = int(key) #motiondetect
#--- Controls ---                 
            elif key=="j": #joke/taunt
                speak.taunt()            
            elif key=="g": #test fire
                turret.fire()
#--- Settings ---                  
            elif key=="i": #fps
                print(cam.getFPS())
                cam.resetFPS()
            elif key=="p": #toggle armed
                turret.armed = not turret.armed
                if turret.armed:
                    speak.say("armed")
                else:
                    speak.say("disarmed")            
            elif key=="n": #toggle noisy
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
            elif key=="-": 
                speak.volume(-.1)
                speak.say("check")            
            elif key=="y": #restart speak
                speak = Speak.Speak()
                speak.say("ok")           
            elif key=="w": #pause display
                cam.resetFPS()
                if not display and os.environ.get('DISPLAY') and int(cfg['camera']['display']):
                    display = True
                    print("- display resumed -")
                else:
                    display = False
                    print("- display paused -")
#--- Tolerance ---
            else: 
                adjustpercent = 0.10 #step +/- percent for manual key adjustments
                adjust = lambda val,sign: val * (1 + (sign*adjustpercent))
                if key=="l" or key=="m": #target sensitivity
                    turret.firesensitivity = adjust(turret.firesensitivity, 1 if key=="l" else -1)
                    cfg['tolerance']['firesensitivity'] = turret.firesensitivity
                if key=="a" or key=="z": #threshhold area
                    track.areathresholdcolor = adjust(track.areathresholdcolor, 1 if key=="a" else -1)
                    cfg['tolerance']['colortrack']['areathreshold'] = track.areathresholdcolor
                if key=="s" or key=="x": #threshhold area
                    track.areathresholdobject = adjust(track.areathresholdobject, 1 if key=="s" else -1)
                    cfg['tolerance']['objecttrack']['areathreshold'] = track.areathresholdobject
                print "Area(Color):", track.areathresholdcolor, "Area(Object):", track.areathresholdobject, "Trigger:", turret.firesensitivity
                    
        
if __name__ == "__main__" :
    #start
    sys.exit(main())
    
