#!/usr/bin/python

import threading
import bluetooth
#import getch

import fcntl, os, sys, termios

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

class Listener():

    def __init__(self, cfg):
        self.ready = threading.Event()
        self.cmdsent = threading.Event()
        self.threadquit = threading.Event()
        self.cmd = ""
        self.usebluetooth = True if int(cfg['controller']['usebluetooth']) else False

    
    def startlisteners(self) :
        if self.usebluetooth:
            self.bluetooththread = threading.Thread(target=self.bluetoothlisten)
            self.bluetooththread.daemon=True
            self.bluetooththread.start()
        self.keyboardthread = threading.Thread(target=self.keyboardlisten)
        self.keyboardthread.daemon=True
        self.keyboardthread.start()
        self.ready.set()

    def reset(self) :
        self.cmdsent.clear()
        self.cmd = ""
        self.ready.set()

    def gotchar(self, ch):
        self.ready.clear()
        self.cmd = ch
        print "Command: ", self.cmd
        self.cmdsent.set()

    def keyboardlisten(self) : 
        print "Keyboard: listening"
        while self.ready.wait() and not self.threadquit.isSet(): 
            self.gotchar(getch()) #getch.getch())
        print "Keyboard: done"

    def bluetoothlisten(self) :
        self.server_sock = bluetooth.BluetoothSocket( bluetooth.RFCOMM )
        self.server_sock.bind(("", 1)) #for controlling device MAC address, run: $sudo rfcomm bind rfcomm0 XX:XX:XX:XX:XX:XX 1
        self.server_sock.listen(1) #1 connection at a time.
        bluetooth.advertise_service( self.server_sock, "BluetoothRobot", "fa87c0d0-afac-11de-8a39-0800200c9a66" )
        print "Bluetooth: Waiting on RFCOMM channel %d" % self.server_sock.getsockname()[1]
        self.sock = None
        self.sock, self.info = self.server_sock.accept()
        print "Bluetooth: listening"
        while self.ready.wait() and not self.threadquit.isSet(): 
            try:
                self.gotchar(self.sock.recv(1024))
            except IOError:
                pass
        print "Bluetooth: done"
        
    def quit(self):
        self.threadquit.set()
        self.ready.set()
        if self.usebluetooth:
            if not self.sock == None:
                self.sock.close()
            self.server_sock.close()


