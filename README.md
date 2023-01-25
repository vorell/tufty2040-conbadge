# tufty2040-conbadge
Fork of tufty2040 demo code from Pimoroni - https://github.com/pimoroni/pimoroni-pico/tree/main/micropython/examples/tufty2040
# Description

This repo is just my personal efforts to extend the functionality of my **tufty2040**. This code is terrible, use at your own discretion. 
There is only a `main.py` python program which provides the following features:
 - Main Badge Display with 98X120 profile picture and 3 lines of text. (Slightly modified Pimoroni Demo code).
 - Entire badge color theme can be altered by editing `LIGHTEST`, `LIGHT`, `DARK`, `DARKEST` variables.
 - Screensaver function that cycles black/white and resets display to main badge. (Doesn't currently interrupt Gallery)
 - Dynamic backlight function (Linear conversion of photoresistor readings)
 - **A** - Gallery function where you can cycle through images in `/gallery` using **up** / **down** buttons. Images are loaded in alphabetical order by file name.
 - **B** - Realtime uptime/battery status display. (Heavily modified variant of Pimoroni's battery.py)
 - **C** - QR Code Display (Pimoroni demo code)
