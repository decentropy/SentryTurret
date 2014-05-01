#!/usr/bin/python

import fcntl
import os
import sys
import termios
import threading

#globals
keypressed = threading.Event()
key = ""
            
def getch():
    fd = sys.stdin.fileno()     
    oldattr = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)     
    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)     
    try:
        while True:
            try:
                c = sys.stdin.read(1)
            except IOError:
                pass
            else:
                return c
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, oldattr)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
        
class WaitKey() :
    def __init__(self):
        global key, keypressed
        keypressed.clear()
        key = ""
        self.thread = threading.Thread(target=self.run)   
    def run(self) :
        global key, keypressed
        key = getch()
        keypressed.set()
