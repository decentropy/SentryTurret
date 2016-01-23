#!/bin/sh

# To autostart bot, add below line to /etc/rc.local
# $ sudo sh <path>/run.sh &

# add bluetooth serial port
sdptool add SP

# bind phone mac address
sudo rfcomm bind rfcomm0 F8:A9:D0:A2:07:25 1

cd /home/pi/bot

#start bot, restarting on error(0)
while true ; do

    # reset bluetooth interface
    sudo hciconfig hci0 reset
    
    #start bot and log
    EXITCODE=`/usr/bin/python main.py >> /home/pi/bot/bot.log 2>&1`
    if [ $? -ne 1 ]; then
        break
    fi
    
    #repair ssh stdin echo
    stty sane
done
