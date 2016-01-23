# SentryTurret

The purpose of this project is to create a cheap autonomous turret, capable of detecting motion and targetting objects.

![Pew Pew](https://raw.githubusercontent.com/steve-vincent/SentryTurret/master/robot.png "Working Example")

## Overview

These instructions were written for constructing the robot with RPi2+RaspiCam+servos, but **you may try it out on a desktop with a webcam** (after installing required python packages).

**The basic structure of the program follows:**
- Main()
    - Spawn Camera() thread to fetch camera frames
    - Spawn Turret() thread to listen and move servos. If centered and armed, will fire.
    - Spawn Controller() thread to listen for input (keyboard or bluetooth)
    - Loop:
        - Get last frame from Camera()
        - If tracking target:
            - Find center of target in frame
            - Give Turret() new target coords
        - Else if searching for target, do one of:
            - Detect face mode
            - Detect motion by color
            - Detect motion by object
        - If input, do command. E.g:
            - Quit
            - Targetting mode
            - Adjust setting
            - etc.

## Install

See [CONFIG.INI](https://github.com/steve-vincent/SentryTurret/blob/master/config.ini)  for settings

### Python Package Requirements
~~~
python-dev
libopencv-dev
python-opencv
open-cv
dlib (see note below)
configobj
python-smbus
webcolors
bluez python-bluetooth python-gobject  (for bluetooth)
pyttsx (for speech)
~~~

**Installing dlib**
While "sudo apt-get install" works for opencv, [dlib](http://dlib.net) (used for object tracking) requires compilation. Here are basic steps to do that:
~~~
sudo apt-get install cmake
Install boost from: http://sourceforge.net/projects/boost
sudo apt-get install libboost-python-dev
wget http://dlib.net/files/dlib-18.18.tar.bz2
tar jxf dlib-18.18.tar.bz2
cd dlib*
sudo python setup.py install
pip install dlib
~~~

### Hardware To Construct Robot
- Raspberry Pi 2 + power supply
- RaspiCam
- PWM Servo Driver + power supply
- 3 standard servos
- Optional: Speaker (for speech feedback)
- Optional: Bluetooth USB adapter (for bluetooth control)
- Robot frame: camera mounted direction of gun, with servos for trigger and pan/tilt rotation

## Usage

`$ python main.py`

See [HELP.TXT](https://github.com/steve-vincent/SentryTurret/blob/master/help.txt)  for commands

## Setup Tips

**Camera:**
For using raspicam with opencv, add bcm2835-v4l2 with `sudo modprobe bcm2835-v4l2` (read [here](http://raspberrypi.stackexchange.com/questions/17068/using-opencv-with-raspicam-and-python)  and [here](https://www.raspberrypi.org/forums/viewtopic.php?f=43&t=94381)).
- CONFIG.INI settings: 
    - upsidedown: how you mount the camera.
    - width,height: camera capture dimensions
    - scaledown: for faster processing/framerate
    - display: on or off to display robot view. (Slower)

**Turret/Servos:**
Here is a [good tutorial](https://learn.adafruit.com/adafruit-16-channel-servo-driver-with-raspberry-pi) on connecting servos with your RPi. (Also read about [setting I2C permissions](http://www.raspberrypi.org/forums/viewtopic.php?p=238003#p238003)).
- CONFIG.INI settings: 
    - panchannel/tiltchannel/triggerchannel: channels on servo driver for each servo
    - fireposition: how far back to pull trigger
    - firesensitivity: how centered before firing? (higher is more "trigger happy")
    - *TODO: These other settings need some clean up or auto-calibration. Tweak if needed.*
        - stepsleep: seconds per microstep
        - pixelsperpulse: you have to manually measure & set this per rotation/camera, (pixels between same point after turret rotates 1.0 pulse.)
        - fps: how fast turret expects coordinates


**Speech:** (Optional)
If you connect a speaker, robot will speak modes and actions. Make sure volume is up the first time: `$ amixer sset PCM,0 100%`. 
- CONFIG.INI settings: 
    - quiet: on or off (turn off if you don't have speaker)

**Controller :** 
Send commands by either: keyboard (direct USB) or bluetooth (USB dongle + android app, such as [BlueMCU](https://play.google.com/store/apps/details?id=com.bluetooth.BlueMCU&hl=en)). Read about [bluetooth setup](https://github.com/metachris/android-bluetooth-spp) and [helpful commands](https://www.raspberrypi.org/forums/viewtopic.php?p=521067).
- CONFIG.INI settings: 
    - usebluetooth: on or off (turn off if you don't use)

E.g. To enable serial port, and connect bluetooth to your phone
~~~
$ sdptool add SP
$ sudo rfcomm bind rfcomm0 XX:XX:XX:XX:XX:XX 1 (<-your address here)
~~~

## Issues and Workarounds

You see a lot of output on start which may be ignored.

Bluetooth may need reset before restarting bot.
~~~
$ sudo hciconfig hci0 reset
~~~

Stdin may stop showing what you type after running. Reset with:
~~~
$ stty sane
~~~

## Contribute

Contributions are welcome to improve accuracy and movement of the robot!

## License

This project licensed under GNU GENERAL PUBLIC LICENSE
https://www.gnu.org/licenses/gpl.txt
