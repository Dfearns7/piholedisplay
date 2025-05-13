#!/usr/bin/env python
# encoding: utf-8

 #  @filename   :   main.cpp
 #  @brief      :   2.13inch e-paper display demo
 #  @author     :   Yehui from Waveshare
 #
 #  Copyright (C) Waveshare     September 9 2017
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy
 # of this software and associated documnetation files (the "Software"), to deal
 # in the Software without restriction, including without limitation the rights
 # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 # copies of the Software, and to permit persons to  whom the Software is
 # furished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 # THE SOFTWARE.
 ##

import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'font')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd2in13b_V4
import time
from time import gmtime, strftime
import PIL
from PIL import Image,ImageDraw,ImageFont
from textwrap import dedent
import requests
import subprocess
import json

logging.basicConfig(level=logging.DEBUG)

api_url = 'http://localhost/api/stats/summary'

font = ImageFont.truetype(os.path.join(fontdir, 'DejaVuSansMono.ttf'), 12)
font_bold = ImageFont.truetype(os.path.join(fontdir, 'DejaVuSansMono-Bold.ttf'), 13)
font_title_bold = ImageFont.truetype(os.path.join(fontdir, 'DejaVuSansMono-Bold.ttf'), 11)
font_debug = ImageFont.truetype(os.path.join(fontdir, 'DejaVuSansMono.ttf'), 8)

def deep_reset(epd):
    logging.info("resetting to white...")
    white_screen = Image.new('1', (epd2in13b_V4.EPD_WIDTH, epd2in13b_V4.EPD_HEIGHT), 255)
    epd.display(epd.getbuffer(white_screen), epd.getbuffer(white_screen))
    epd.delay_ms(1000)

def update(epd):

    # EPD 2 inch 13 b HAT is rotated 90 clockwize and does not support partial update
    # But has amazing 2 colors
    logging.info("drawing status")
    width = epd2in13b_V4.EPD_HEIGHT
    height = epd2in13b_V4.EPD_WIDTH
    top = 2
    fill_color = 0
    xt = 70
    xc = 120
    xc2 = 170

    while True:
        frame_black = Image.new('1', (width, height), 255)
        frame_red = Image.new('1', (width, height), 255)

        pihole_logo_top = Image.open(os.path.join(picdir, 'pihole-bw-80-top.bmp'))
        pihole_logo_bottom = Image.open(os.path.join(picdir, 'pihole-bw-80-bottom.bmp'))

        draw_black = ImageDraw.Draw(frame_black)

        draw_black.rectangle((0, 0, width, height), outline=0, fill=None)

        ip = subprocess.check_output( "hostname -I | cut -d' ' -f1", shell=True).strip()
        ip = ip.decode("utf-8")
        logging.info("ip:%s" % ip)
        host = subprocess.check_output("hostname", shell=True).strip().decode() + ".local"
        logging.info("host:%s" % host)
        mem_usage = subprocess.check_output(dedent("""
             free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'
             """), shell=True)
        mem_usage = mem_usage.decode("utf-8").replace("Mem: ", "")
        logging.info("memory usage:%s" % mem_usage)
        disk = subprocess.check_output(dedent("""
            df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'
            """).strip(), shell=True)
        disk = disk.decode("utf-8").replace("Disk: ", "")
        logging.info("disk:%s" % disk)
        
        try:
            r = requests.get(api_url)
            data = json.loads(r.text)
            dnsqueries = data['queries']['total']
            adsblocked = data['queries']['blocked']
            clients = data['clients']['active']
        except KeyError:
            time.sleep(1)
            continue

        frame_black.paste(pihole_logo_top, (-8, 2))
        frame_red.paste(pihole_logo_bottom, (-8, 2))
        draw_red = ImageDraw.Draw(frame_red)
        draw_red.text((10, height - 21), "Pi", font=font_title_bold, fill=fill_color)
        draw_red.text((23, height - 21), "-hole", font=font_title_bold, fill=fill_color)

        draw_black.text((xt, top + 0), "HOST: ", font=font_bold, fill=fill_color)
        draw_black.text((xc, top + 0), host, font=font, fill=fill_color)
        draw_black.text((xt, top + 16), "IP: ", font=font_bold, fill=fill_color)
        draw_black.text((xc, top + 16), str(ip), font=font, fill=fill_color)
        draw_black.text((xt, top + 32), "Mem:",  font=font_bold, fill=fill_color)
        draw_black.text((xc, top + 32), str(mem_usage),  font=font, fill=fill_color)
        draw_black.text((xt, top + 48), "Disk:",  font=font_bold, fill=fill_color)
        draw_black.text((xc, top + 48),  str(disk),  font=font, fill=fill_color)
        draw_black.text((xt, top + 64), "Ads Blocked: ", font=font_bold, fill=fill_color)
        draw_black.text((xc2, top + 64), str(adsblocked), font=font, fill=fill_color)
        draw_black.text((xt, top + 80), "Clients:", font=font_bold, fill=fill_color)
        draw_black.text((xc2, top + 80), str(clients), font=font, fill=fill_color)
        draw_black.text((xt, top + 96), "DNS Queries: ", font=font_bold, fill=fill_color)
        draw_black.text((xc2, top + 96), str(dnsqueries), font=font, fill=fill_color)

        draw_black.text((14, height - 10), u"↻: ", font=font, fill=fill_color)
        draw_black.text((24, height - 8), strftime("%H:%M", gmtime()), font=font_debug, fill=fill_color)

        epd.display(epd.getbuffer(frame_black.transpose(PIL.Image.ROTATE_180)),
                          epd.getbuffer(frame_red.transpose(PIL.Image.ROTATE_180)))
        sleep_sec = 10 * 60
        logging.info("sleeping {0} sec ({1} min) at {1}".format(sleep_sec, sleep_sec / 60,
                                                         strftime("%H:%M", gmtime())))
        epd.sleep()
        epd.delay_ms(sleep_sec * 1000)
        # awakening the display
        epd.init()

def main():
    logging.info("initing screen...")
    epd = epd2in13b_V4.EPD()
    epd.init()
    try:
        update(epd)
    finally:
        logging.info("sleeping epd before leaving")
        epd.sleep()

if __name__ == '__main__':
    main()