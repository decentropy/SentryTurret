#!/usr/bin/python

#used if no servos connected


class PWM :

  def __init__(self, address=0x40, debug=False):
    self.test = True

  def setPWMFreq(self, freq):
    self.test = True
    
  def setPWM(self, channel, on, off):
    self.test = True
