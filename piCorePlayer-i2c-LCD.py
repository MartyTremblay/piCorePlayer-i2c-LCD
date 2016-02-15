#!/usr/bin/env python
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('./PyLMS')
sys.path.append('./RPi_I2C_driver')
from time import sleep
import textwrap
import subprocess
from uuid import getnode as get_mac 
from pylms.server import Server
from pylms.player import Player
import RPi_I2C_driver

global lcd_first_line
global lcd_second_line
global mylcd
global sq
global clear_line
global lcd_char_width

fontdata = [
    # Char 0  - 0%
    [0x00,0x01,0x00,0x00,0x01,0x00,0x00,0x01],
    # Char 1 - 14%
    [0x00,0x01,0x00,0x00,0x01,0x00,0x00,0x03],
    # Char 2 - 28%
    [0x00,0x01,0x00,0x00,0x01,0x00,0x02,0x03],
    # Char 3 - 43%
    [0x00,0x01,0x00,0x00,0x01,0x02,0x02,0x03],
    # Char 4 - 57%
    [0x00,0x01,0x00,0x00,0x03,0x02,0x02,0x03],
    # Char 5 - 71%
    [0x00,0x01,0x00,0x02,0x03,0x02,0x02,0x03],
    # Char 6 - 85%
    [0x00,0x01,0x02,0x02,0x03,0x02,0x02,0x03],
    # Char 7 - 100%
    [0x00,0x05,0x04,0x04,0x05,0x04,0x04,0x05],

    # Char 8 - play
    [0x00,0x00,0x00,0x08,0x0c,0x0e,0x0c,0x08],
    # Char 9 - paused
    [0x00,0x00,0x00,0x1b,0x1b,0x1b,0x1b,0x1b],
    # Char 10 - stop
    [0x00,0x00,0x00,0x1f,0x1f,0x1f,0x1f,0x1f],
    # Char 11 - progress
    [0x00,0x00,0x00,0x00,0x00,0x15,0x00,0x00],
]

lcd_char_width = 16
clear_line = " " * lcd_char_width
lcd_first_line = ""
lcd_second_line = ""

mylcd = RPi_I2C_driver.lcd()
mylcd.lcd_load_custom_chars(fontdata)

#ip = "192.168.101.12"
ip = ""
print "Using squeezelite to obtain ip address of server..."	
while ip == "":
    try:
        ip = subprocess.check_output("netstat -tn  | grep 3483 | /usr/bin/awk -v col=5 '{split($col,a,\":\"); print a[1]}'", shell=True)
    except:
        sleep(1)
print "Server: " + ip

sc = Server(hostname=ip, port=9090, username="", password="")
sc.connect()

print "Logged in: %s" % sc.logged_in
print "Version: %s" % sc.get_version()

mac = ':'.join(['{:02x}'.format((get_mac()  >> i) & 0xff) for i in range(0,8*6,8)][::-1])
print  mac                                        
sq = sc.get_player(mac)
#mylcd.lcd_display_string("".join(sq.get_ip_address()).center(lcd_char_width), 1)
#mylcd.lcd_display_string("".join(sq.get_name()).center(lcd_char_width), 2)

#sleep(3) 

def print_progress_bar() :
    global mylcd, sq, lcd_char_width, clear_line, lcd_second_line
    #lcd_text = ""
    if sq.get_mode() == "pause" :
        mylcd.lcd_display_string_pos(unichr(9),2,0)
    elif sq.get_mode() == "stop" :
        mylcd.lcd_display_string_pos(unichr(10),2,0)
    elif sq.get_track_duration() > 0 : 
        percentage_played = float(sq.get_time_elapsed()) / float(sq.get_track_duration())
        lcd_text = unichr(11) * int(percentage_played * (lcd_char_width - 1)) + " "
        #if lcd_text != lcd_second_line :
        lcd_second_line = lcd_text
        mylcd.lcd_display_string_pos(unichr(8) + lcd_text, 2, 0)
        mylcd.lcd_display_string_pos(unichr(int(sq.get_volume() * .07)),2,15)
        #print int(sq.get_volume() * .05)
    else :
        lcd_text = "Streaming".center(lcd_char_width)
    
    


def print_time_remaining() :
    global mylcd, sq, lcd_char_width, clear_line, lcd_second_line
    
    if sq.get_mode() == "pause" :
        lcd_text = "Paused".center(lcd_char_width)
    elif sq.get_mode() == "stop" :
        lcd_text = "Stopped".center(lcd_char_width)
    else: 
        seconds = int(sq.get_time_remaining())
        minutes = int(seconds/60)
        seconds = seconds - (minutes * 60)
        if seconds < 10 :
            seconds = "0".join(seconds)
        if minutes < 10 :
            minutes = " ".join(minutes)
        lcd_text = "     %s : %s     " % ( minutes, seconds )
    mylcd.lcd_display_string(lcd_text, 2) 
    
    
def run() :
    global mylcd, sq, lcd_char_width, clear_line, lcd_second_line
    display = "%s - %s" % (sq.get_track_artist(), sq.get_track_title())
    dedented_text = textwrap.dedent(display)
    lcd_text = textwrap.fill(dedented_text, 1)  
    text = dedented_text
    text = "                            %s " % text       
    for i in range (12, (len(text)-1)):

        # too taxing on raspberry pi B+, turn it back on for B2?
        #if (i % 2 == 0) :
            #print_time_remaining()
            
        if (i % 6 == 0) :
            # instead of time_remaining, print progress bar. much easier on the CPU
            print_progress_bar()

            if display != "%s - %s" % (sq.get_track_artist(), sq.get_track_title()) :
                mylcd.lcd_display_string("".center(lcd_char_width), 2)
                break
        
        scroll_text = text[i:(i+lcd_char_width)]  
        sleep(.3) 
        
        mylcd.lcd_display_string(scroll_text, 1)

while not "100%" in (  subprocess.Popen(["ping", "-c1", "-W1", ip], stdout=subprocess.PIPE).stdout.read() ) : 
    while sq.get_power_state() == True :
        run()
    sleep (1)