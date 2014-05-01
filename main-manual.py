#!/usr/bin/env python

import threading
import numpy as np
import cv2
from time import sleep
import Turret
import Capture

#global
gexit = 0
turret = Turret.Controller()
turret.daemon = True
turret.recenter()
turret.start()

class MyDims():  
    def __init__(self):
        self.scaledown = 2.0 #shrink for processing speed
        self.displayscaledown = 2.0 #shrink for display speed
        self.pixelPulseRatio = 866.0/self.scaledown # cam image measured: 433px=.5 pulse
    def camDims(self, w, h):
        self.w = w
        self.h = h
        self.wmiddle = self.w/2.0
        self.hmiddle = self.h/2.0
        self.scalebackup = self.scaledown/self.displayscaledown
        self.displayw = int(self.w * self.scalebackup)
        self.displayh = int(self.h * self.scalebackup)
    def coordToPulse(self, coord):
        xpulse = (float(coord[0]) - self.wmiddle) / self.pixelPulseRatio
        ypulse = (self.hmiddle - float(coord[1])) / self.pixelPulseRatio
        return (xpulse,ypulse)
        
def on_click(event, cx, cy, flag, param):
    global gexit
    if(event==cv2.cv.CV_EVENT_LBUTTONDOWN):
        print cx,cy
        coords = (cx,cy)
        newturr = dims.coordToPulse(coords)
        currturr = (turret.xy[0],turret.xy[1])
        turret.sendTarget(newturr, currturr)   
    if(event==cv2.cv.CV_EVENT_MBUTTONDOWN):
        turret.fire()
    if(event==cv2.cv.CV_EVENT_RBUTTONDOWN):
        print "exiting..."
        gexit = 1

cv2.namedWindow("camera", 1)
cv2.setMouseCallback("camera",on_click, 0)

dims = MyDims()
cam = Capture.Cam()
cam.scale(dims.scaledown)
dims.camDims(cam.w, cam.h)

while not gexit == 1:
    sleep(.1)     
    cam.getFrame()
    cv2.imshow("camera", cam.frame)
    cv2.waitKey(1)
    
