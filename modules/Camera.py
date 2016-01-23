#!/usr/bin/python

import threading
import cv2
import datetime

class Capture(threading.Thread) :

    def __init__(self, cfg):
        threading.Thread.__init__(self)
        self.upsidedown = int(cfg['camera']['upsidedown'])  
        self.w = int(cfg['camera']['width']) 
        self.h = int(cfg['camera']['height'])    
        #for faster processing
        self.scaledown = float(cfg['camera']['scaledown']) 
        self.w = int(self.w / self.scaledown)
        self.h = int(self.h / self.scaledown)
        #for fps
        self.rawframe = None
        self.frametime = None
        self.framecount = 0
        self.stopped = False
        

    def run(self):
        #loop to always get latest frame        
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.w) #TODO: does this work webcam?
        self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.h)       
        while True:
            if self.stopped:
                return
            _, self.rawframe = self.capture.read()
            self.frametime = datetime.datetime.now()        

        
    def getFrame(self):
        frame = self.rawframe
        self.framecount = self.framecount + 1
#        if self.scaledown != 1: 
#            frame = cv2.resize(self.rawframe, (self.w, self.h)) #TODO: only if needed
         #if cam mounted upside down, rotate 180
        if self.upsidedown: #TODO: do this in display, but for coords with math
            M = cv2.getRotationMatrix2D((self.w/2, self.h/2), 180, 1.0)
            frame = cv2.warpAffine(frame, M, (self.w, self.h)) 
        return frame
    
    def getFPS(self): 
        return str(self.framecount / (self.starttime - datetime.datetime.now()).total_seconds())
    
    def resetFPS(self): 
        self.starttime = datetime.datetime.now()
        self.framecount = 0
			
    def quit(self):
		self.stopped = True
		self.capture.release()


