#!/usr/bin/python

#sudo apt-get install espeak

#import threading
import webcolors
import pyttsx
import random

class Speak():
    def __init__(self, cfg):
        self.cfg = cfg
        self.engine = pyttsx.init()
        self.engine.setProperty('rate', int(cfg['speak']['rate']))
        self.engine.setProperty('speak', cfg['speak']['dialect'])
        self.engine.setProperty('volume', float(cfg['speak']['volume']))
        self.quiet = int(cfg['speak']['quiet'])
        self.taunts = cfg['speak']['taunts']
        self.tauntidx = random.randint(0, len(self.taunts)-1) #first taunt
    def say(self, msg):
        print "*** ROBOT ***: \"" + msg + "\""
        if not self.quiet:
            self.engine.say(msg)
            self.engine.runAndWait()
    def volume(self, val):
        currvol = float(self.engine.getProperty('volume'))
        vol = currvol + val
        if (0.0 <= vol <= 1.0):
            print "volume:", vol
            self.engine.setProperty('volume', vol)
            self.cfg['speak']['volume'] = vol
    def taunt(self):
        self.say(self.taunts[self.tauntidx])
        if self.tauntidx < (len(self.taunts)-1):
            self.tauntidx = self.tauntidx + 1
        else:
            self.tauntidx = 0   
            
def BGRname(bgrcolor):
    print "rgb = ", bgrcolor[2], bgrcolor[1], bgrcolor[0]
    try:
        closest_name = webcolors.rgb_to_name((bgrcolor[2], bgrcolor[1], bgrcolor[0]))
    except ValueError:
        min_colors = {}
        for key, name in webcolors.css21_hex_to_names.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(key)
            bd = (b_c - bgrcolor[0]) ** 2
            gd = (g_c - bgrcolor[1]) ** 2
            rd = (r_c - bgrcolor[2]) ** 2
            min_colors[(rd + gd + bd)] = name
        closest_name =  min_colors[min(min_colors.keys())]
    return closest_name


