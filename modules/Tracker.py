#!/usr/bin/python

import cv2
import numpy as np
import math

class Tracking() :

    def __init__(self, cfg, display):
        self.display = display
        self.mode = 0 # 0:waiting, 1:faceshirthsv, 2:motionhsv, 3:motionobj, 4:hsvtarget
        #facetrack  
        self.facecascade = None
        #objtrack  
        self.areathresholdobject = int(cfg['tolerance']['objecttrack']['areathreshold']) / float(cfg['camera']['scaledown'])
        #colortrack
        self.areathresholdcolor = int(cfg['tolerance']['colortrack']['areathreshold']) / float(cfg['camera']['scaledown'])
        self.hsvtarget = None #HSV range: 0-180,255,255
        self.hsvtolerance = [float(cfg['tolerance']['colortrack']['hue']),
                             float(cfg['tolerance']['colortrack']['saturation']),
                             float(cfg['tolerance']['colortrack']['value'])]
        self.bgrtarget = None #for display only
                             
                    
    def setColorRange(self):
        self.hsvlower = np.array([max(0,self.hsvtarget[0] - self.hsvtolerance[0]), 
                                  max(0,self.hsvtarget[1] - self.hsvtolerance[1]), 
                                  max(0,self.hsvtarget[2] - self.hsvtolerance[2])], dtype=np.uint8)
        self.hsvupper = np.array([min(180,self.hsvtarget[0] + self.hsvtolerance[1]), 
                                  min(255,self.hsvtarget[1] + self.hsvtolerance[1]), 
                                  min(255,self.hsvtarget[2] + self.hsvtolerance[2])], dtype=np.uint8)
        print "Target: Hue(",self.hsvlower[0],self.hsvupper[0],") Sat(",self.hsvlower[1],self.hsvupper[1],") Val(",self.hsvlower[2],self.hsvupper[2],")"
                                  

    def getBestContour(self, imgmask, threshold):
        contours,hierarchy = cv2.findContours(imgmask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        best_cnt = None
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > threshold:
                threshold = area
                best_cnt = cnt   
        return best_cnt


    def getMotionContour(self, frame, resframe, threshold):
        #mask all motion
        motionmask = cv2.absdiff(frame, resframe)
        motionmask = cv2.cvtColor(motionmask, cv2.COLOR_RGB2GRAY)
        _,motionmask = cv2.threshold(motionmask, 25, 255, cv2.THRESH_BINARY)
        cntmask = motionmask.copy()
        cnt = self.getBestContour(cntmask, threshold)
        return cnt, motionmask
        
        
    def targetHsv(self, frame):
        #find best contour in hsv range
        displayframe = None
        framehsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        framemask = cv2.inRange(framehsv, self.hsvlower, self.hsvupper)
        if self.display: #color copy
            displaymaskframe = cv2.cvtColor(framemask.copy(), cv2.COLOR_GRAY2BGR)
            displayframe = cv2.addWeighted(frame, 0.7, displaymaskframe, 0.3, 0)
        best_cnt = self.getBestContour(framemask, self.areathresholdcolor)  
        if not best_cnt == None: #if match found
            #get center
            M = cv2.moments(best_cnt)
            cx,cy = int(M['m10']/M['m00']), int(M['m01']/M['m00'])   
            if self.display:
                #display circle target
                objcenter = (cx,cy)
                objradius = int(round(math.sqrt(cv2.contourArea(best_cnt)),2))
                cv2.circle(displayframe, objcenter, objradius, (0,0,0), 5)
                cv2.circle(displayframe, objcenter, objradius, self.bgrtarget, 3)
            return cx, cy, displayframe
        else:
            return None, None, frame
                    



