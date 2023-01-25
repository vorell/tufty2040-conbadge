# A retro badge with photo and QR code.
# Copy your image to your Tufty alongside this example - it should be a 98 x 120 jpg.

from picographics import PicoGraphics, DISPLAY_TUFTY_2040
from pimoroni import Button
from machine import ADC, Pin, Timer
from time import sleep
import os
import machine
import time
import jpegdec
import qrcode
#import _thread

# define display constraints
display = PicoGraphics(display=DISPLAY_TUFTY_2040)

# define display bounds
WIDTH, HEIGHT = display.get_bounds()

# define RTC & startup time
rtc = machine.RTC()
startup_time = time.time()

# define timers
backlight_timer = Timer(period=500, mode=Timer.PERIODIC, callback=lambda t:adjust_backlight())
screensaver_timer = Timer(period=300000, mode=Timer.PERIODIC, callback=lambda t:reset_badge())
    
# define buttons
button_a = Button(7, invert=False)
button_b = Button(8, invert=False)
button_c = Button(9, invert=False)
button_up = Button(22, invert=False)
button_down = Button(6, invert=False)
#button_boot = Button(23, invert=True)

# define gallery images
# PUT YOUR GALLERY JPGS INTO "/gallery" FOR ENUMERATION HERE
gallery_folder = "/gallery"
gallery_files = os.ilistdir("/gallery")
gallery_images = []
for entry in gallery_files:
    if entry[1] == 0x8000:
        filename = entry[0]
        gallery_images.append(gallery_folder + "/" + filename)
        
# Count the number of images in gallery
gallery_size = len(gallery_images)
            
# define light sensor
# value range is 160-59470
# range ~59310
lux_pwr = Pin(27, Pin.OUT)
lux_pwr.value(1)
lux = ADC(26)

# define values used for adjust_backlight linear conversion
# visible values .33 thru 1.0
# range .67
# NewValue = (((OldValue - OldMin) * NewRange) / OldRange) + NewMin
luxValue = lux.read_u16()
luxMax = 59470
luxMin = 160
backlightMax = 1.0
backlightMin = 0.33
luxRange = luxMax - luxMin
luxRangeFloat = 1 / luxRange
backlightRange = backlightMax - backlightMin

# 2bit Demichrome colour palette by Space Sandwich - https://lospec.com/palette-list/2bit-demichrome
LIGHTEST = display.create_pen(233, 239, 236)
LIGHT = display.create_pen(160, 160, 139)
DARK = display.create_pen(85, 85, 104)
DARKEST = display.create_pen(33, 30, 32)

# setup some colors to draw with
GREEN = display.create_pen(0, 255, 0)
RED = display.create_pen(255, 0, 0)
    
# change your badge and QR details here!
COMPANY_NAME = "COMPANY NAME"
NAME = "YOUR NAME"
BLURB1 = "SOME TEXT"
BLURB2 = "MORE TEXT"
BLURB3 = "EVEN MOAR"

QR_TEXT = "put your url here"

IMAGE_NAME = "badge.jpg"

# some constants we'll use for drawing
BORDER_SIZE = 4
PADDING = 10
COMPANY_HEIGHT = 40

def adjust_backlight():
    luxValue = lux.read_u16()
    backlightValue = ((((luxValue - luxMin) * backlightRange) * luxRangeFloat) + backlightMin)
    if backlightValue <= 0.90:
        backlightValue = backlightValue + 0.10
    display.set_backlight(backlightValue)
    
def draw_battery():
    # setup the ADCs for measuring battery voltage
    vbat_adc = ADC(29)
    vref_adc = ADC(28)
    usb_power = Pin(24, Pin.IN)         # reading GP24 tells us whether or not USB power is connected

    # reference voltages for a full/empty battery, in volts
    # the values could vary by battery size/manufacturer so you might need to adjust them
    # values for a Galleon 400mAh LiPo:
    full_battery = 3.87
    empty_battery = 2.5

    # define some display options including font
    display.set_font("bitmap8")
    
    # calculate the logic supply voltage, as will be lower that the usual 3.3V when running off low batteries
    vdd = 1.24 * (65535 / vref_adc.read_u16())
    vbat = (
        (vbat_adc.read_u16() / 65535) * 3 * vdd
    )  # 3 in this is a gain, not rounding of 3.3V

    # print out the voltage
    #print("Battery Voltage = ", vbat, "V", sep="")

    # convert the raw ADC read into a voltage, and then a percentage
    percentage = 100 * ((vbat - empty_battery) / (full_battery - empty_battery))
    if percentage > 100:
        percentage = 100
    if percentage < 0:
        percentage = 0

    # draw border
    display.set_pen(LIGHTEST)
    display.clear()

    # draw background
    display.set_pen(DARK)
    display.rectangle(BORDER_SIZE, BORDER_SIZE, WIDTH - (BORDER_SIZE * 2), HEIGHT - (BORDER_SIZE * 2))
    
    # define constraints of battery graphics
    battery_xstart = 50
    battery_ystart = 50
    battery_width = 220
    battery_height = 140
    lvl_bg_width = 214
    lvl_bg_height = 129
    bat_lvl_width = int((210 / 100) * percentage)
    bat_lvl_height = 125
    
    # draw the battery outline
    display.set_pen(DARKEST)
    display.rectangle(battery_xstart, battery_ystart, battery_width, battery_height)
    display.rectangle((battery_xstart+battery_width), int((battery_height+battery_ystart)/2), 20, 55)
    display.set_pen(LIGHTEST)
    display.rectangle((battery_xstart+3), (battery_ystart+3), lvl_bg_width, lvl_bg_height)

    # draw a green box for the battery level
    display.set_pen(GREEN)
    display.rectangle((battery_xstart+5), (battery_ystart+5), bat_lvl_width, bat_lvl_height)

    # add battery text
    display.set_pen(DARK)
    if usb_power.value() == 1:         # if it's plugged into USB power...
        display.text("USB power!", (battery_xstart+15), (battery_ystart+90), 240, 4)

    display.text('{:.2f}'.format(vbat) + "v", (battery_xstart+15), (battery_ystart+10), 240, 5)
    display.text('{:.0f}%'.format(percentage), (battery_xstart+15), (battery_ystart+50), 240, 5)
    
    # add uptime text
    display.set_pen(LIGHTEST)
    display.text("Uptime", (battery_xstart+50), (battery_ystart+150), 160, 2)
    hour,minute = get_uptime()
    display.text('{:02}:{:02}'.format(hour, minute), 165, 200, 160, 2)
    display.update()
    
def draw_badge():
    # draw border
    display.set_pen(LIGHTEST)
    display.clear()

    # draw background
    display.set_pen(DARK)
    display.rectangle(BORDER_SIZE, BORDER_SIZE, WIDTH - (BORDER_SIZE * 2), HEIGHT - (BORDER_SIZE * 2))

    # draw company box
    display.set_pen(DARKEST)
    display.rectangle(BORDER_SIZE, BORDER_SIZE, WIDTH - (BORDER_SIZE * 2), COMPANY_HEIGHT)

    # draw company text
    display.set_pen(LIGHT)
    display.set_font("bitmap6")
    display.text(COMPANY_NAME, BORDER_SIZE + PADDING, BORDER_SIZE + PADDING, WIDTH, 3)

    # draw name text
    display.set_pen(LIGHTEST)
    display.set_font("bitmap8")
    display.text(NAME, BORDER_SIZE + PADDING, BORDER_SIZE + PADDING + COMPANY_HEIGHT, WIDTH, 5)

    # draws the bullet points
    display.set_pen(DARKEST)
    display.text("*", BORDER_SIZE + PADDING + 98 + PADDING, 105, 160, 2)
    display.text("*", BORDER_SIZE + PADDING + 98 + PADDING, 140, 160, 2)
    display.text("*", BORDER_SIZE + PADDING + 98 + PADDING, 175, 160, 2)

    # draws the blurb text (4 - 5 words on each line works best)
    display.set_pen(LIGHTEST)
    display.text(BLURB1, BORDER_SIZE + PADDING + 108 + PADDING, 105, 160, 2)
    display.text(BLURB2, BORDER_SIZE + PADDING + 108 + PADDING, 140, 160, 2)
    display.text(BLURB3, BORDER_SIZE + PADDING + 108 + PADDING, 175, 160, 2)

def show_photo():
    j = jpegdec.JPEG(display)

    # open the JPEG file
    j.open_file(IMAGE_NAME)

    # draw a box around the image
    display.set_pen(DARKEST)
    display.rectangle(PADDING, HEIGHT - ((BORDER_SIZE * 2) + PADDING) - 120, 98 + (BORDER_SIZE * 2), 120 + (BORDER_SIZE * 2))

    # decode the JPEG
    j.decode(BORDER_SIZE + PADDING, HEIGHT - (BORDER_SIZE + PADDING) - 120)
    
    # draw BAT button label
    display.set_pen(LIGHTEST)
    display.text("BAT", 145, 215, 160, 2)
    
    # draw QR button label
    display.set_pen(LIGHTEST)
    display.text("QR", 242, 215, 160, 2)
    
def measure_qr_code(size, code):
    w, h = code.get_size()
    module_size = int(size / w)
    return module_size * w, module_size

def draw_qr_code(ox, oy, size, code):
    size, module_size = measure_qr_code(size, code)
    display.set_pen(LIGHTEST)
    display.rectangle(ox, oy, size, size)
    display.set_pen(DARKEST)
    for x in range(size):
        for y in range(size):
            if code.get_module(x, y):
                display.rectangle(ox + x * module_size, oy + y * module_size, module_size, module_size)

def reset_badge():
    try: # unload battery display if open.
        battery_timer.deinit()
    except NameError:
        # do nothing
        pass
    # reset display with dark and light cycle to prevent burn-in
    display.set_pen(DARKEST)
    display.clear()
    display.update()
    display.set_pen(LIGHTEST)
    display.clear()
    display.update()
    badge_mode = "photo"
    draw_badge()
    show_photo()
    display.update()
    
def show_qr():
    display.set_pen(DARK)
    display.clear()

    code = qrcode.QRCode()
    code.set_text(QR_TEXT)

    size, module_size = measure_qr_code(HEIGHT, code)
    left = int((WIDTH // 2) - (size // 2))
    top = int((HEIGHT // 2) - (size // 2))
    draw_qr_code(left, top, HEIGHT, code)

#def background_thread():
    # Undefined presently

def get_uptime():
    now = time.time()
    uptime = (now - startup_time)
    if uptime > 60:
        minutes = uptime // 60
    else:
        minutes = 0
    if minutes > 60:
        hours = minutes // 60
        minutes = minutes % 60
    else:
        hours = 0
        
    return hours, minutes 
        
def show_image(index):
    # set the background color
    display.set_pen(DARKEST)
    display.clear()
    
    j = jpegdec.JPEG(display)

    # open the JPEG file
    j.open_file(gallery_images[index])
    
    # decode the JPEG
    j.decode()
    display.update()
            
# begin program logic

# execute background thread
#_thread.start_new_thread(background_thread, ())

# draw the badge for the first time
badge_mode = "photo"
draw_badge()
show_photo()
display.update()
while True:
    if button_a.is_pressed:
        try: # unload battery display if open.
            battery_timer.deinit()
        except NameError:
            # do nothing
            pass
        if badge_mode == "photo":
            badge_mode = "gallery"
            img_index = 0
            show_image(img_index)
            # logic for browsing gallery
            while badge_mode == "gallery":
                show_image(img_index)
                display.update()
                if button_up.is_pressed:
                    if ((img_index + 1)>(gallery_size - 1)):
                        img_index = 0
                    else:
                        img_index += 1
                elif button_down.is_pressed:
                    if (img_index > 0):
                        img_index -= 1
                    else:
                        img_index = (gallery_size - 1)
                elif button_a.is_pressed:
                    badge_mode = "photo"
                    time.sleep(0.5)
                    reset_badge()
                else:
                    img_index = img_index
        else:
            badge_mode = "photo"
            draw_badge()
            show_photo()
            display.update()
        time.sleep(0.5)
    elif button_b.is_pressed:
        if badge_mode == "photo":
            badge_mode = "bat"
            battery_timer = Timer(period=1000, mode=Timer.PERIODIC, callback=lambda t:draw_battery())
        else:
            badge_mode = "photo"
            battery_timer.deinit()
            draw_badge()
            show_photo()
            display.update()
        time.sleep(0.5)
    elif button_c.is_pressed:
        try: # unload battery display if open.
            battery_timer.deinit()
        except NameError:
            # do nothing
            pass
        if badge_mode == "photo":
            badge_mode = "qr"
            show_qr()
            display.update()
        else:
            badge_mode = "photo"
            draw_badge()
            show_photo()
            display.update()
        time.sleep(0.5)





