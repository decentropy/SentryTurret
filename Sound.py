#!/usr/bin/python

import threading
import os

class Play(threading.Thread):
    def __init__(self, filename):
        self.filename = filename
        self.thread = threading.Thread(target=self.run)
    def run(self):
        cmd = "aplay "+self.filename
        print cmd
        f = os.popen(cmd)
