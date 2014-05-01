#!/usr/bin/python

import cv2

class Cam() :   
    def __init__(self):
        self.capture = cv2.VideoCapture(0)
        self.w = int(self.capture.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
        self.h = int(self.capture.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
    def quit(self):
        self.capture.release()
    def scale(self, scaledown): #for faster processing
        self.w = int(self.w/scaledown)
        self.h = int(self.h/scaledown)
    def getFrame(self):
        _,frame = self.capture.read()
        self.frame = cv2.resize(frame, (self.w, self.h))
