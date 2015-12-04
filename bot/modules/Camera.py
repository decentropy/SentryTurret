#!/usr/bin/python

import cv2

class Capture() :

    def __init__(self, cfg):
        self.w = int(cfg['camera']['width']) 
        self.h = int(cfg['camera']['height']) 
        self.scaledown = float(cfg['camera']['scaledown']) 
        self.upsidedown = int(cfg['camera']['upsidedown']) 
        
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.w)
        self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.h)
        
        #for faster processing
        self.w = int(self.w / self.scaledown)
        self.h = int(self.h / self.scaledown)
        
    def getFrame(self):
        _,frame = self.capture.read()        
        self.frame = cv2.resize(frame, (self.w, self.h))
         #if cam mounted upside down, rotate 180
        if self.upsidedown:
            M = cv2.getRotationMatrix2D((self.w/2, self.h/2), 180, 1.0)
            self.frame = cv2.warpAffine(frame, M, (self.w, self.h))
        
    def quit(self):
        self.capture.release()
