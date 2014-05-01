SentryTurret
============
This project licensed under GNU GENERAL PUBLIC LICENSE
https://www.gnu.org/licenses/gpl.txt

A sentry turret style robot which will detect motion, then track and fire at the object. The robot's "turret" is rotated by two servos (X/pan axis and Y/tilt axis). The "eye"(webcam) and "gun" of the robot should be mounted on the turret. The third servo is attached to pull the trigger when the target centered.

See a working example: http://youtu.be/bgmDVvE1pLw

When activated, the robot will initialize an average image and wait to detect motion above a threshold size. It will target the mean HSV of a moving object and begin blob detection to camera's view (using turret servos) on the object. If the object is centered, it will fire by pulling the trigger servo. 

See main.py for further comments.

To run with display: $python main.py 1
The program starts a thread for the turret which is continually updated with target coordinates by the OpenCV frame processing. A separate thread handles terminal keyboard input:
q = quit
' ' = reset
1 = start motion detect
2 = sample center for target
f/v = +/- threshhold area
a,s,d/z,x,c = +/- H,S,V
p = toggle armed
l/m = +/- target sensitivity

============

The working example was built on RaspberryPi with Raspian and OpenCV(python) 2.4, using GPIO pins connected to a servo driver and servos from Adafruit. Tutorial here: https://learn.adafruit.com/adafruit-16-channel-servo-driver-with-raspberry-pi
As of 5/1/2014, I believe a BeagleBone Black would be preferable platform due to faster CPU and on-board PWM outputs (meaning no separate servo driver needed).

