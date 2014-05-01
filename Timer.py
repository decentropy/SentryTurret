#!/usr/bin/python

import threading
from time import sleep

class Countdown(threading.Thread):
    def __init__(self, seconds, event):
        self.runTime = seconds
        self.event = event
        self.thread = threading.Thread(target=self.run)
    def run(self):
        if not self.event.isSet():
            self.event.set()
            sleep(self.runTime)
            self.event.clear()
