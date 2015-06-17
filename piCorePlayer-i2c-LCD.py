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

lcd_char_width = 16
clear_line = " " * lcd_char_width
lcd_first_line = ""
lcd_second_line = ""

mylcd = RPi_I2C_driver.lcd()
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
mylcd.lcd_display_string("".join(sq.get_ip_address()).center(lcd_char_width), 1)
mylcd.lcd_display_string("".join(sq.get_name()).center(lcd_char_width), 2)

sleep(3) 

def print_progress_bar() :
    global mylcd, sq, lcd_char_width, clear_line, lcd_second_line
    lcd_text = ""
    if sq.get_mode() == "pause" :
        lcd_text = "Paused".center(lcd_char_width)
    elif sq.get_mode() == "stop" :
        lcd_text = "Stopped".center(lcd_char_width)
    elif sq.get_track_duration() > 0 : 
        percentage = float(sq.get_time_elapsed()) / float(sq.get_track_duration())
        lcd_text = "." * int(percentage * lcd_char_width) + "                "
    else :
        lcd_text = "Streaming".center(lcd_char_width)
    
    if lcd_text != lcd_second_line :
        lcd_second_line = lcd_text
        mylcd.lcd_display_string(lcd_text, 2)


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