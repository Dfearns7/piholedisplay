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
# Set up directories
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'font')
if os.path.exists(libdir):
    sys.path.append(libdir)

import math
import logging
import time
from time import strftime
from textwrap import dedent
import requests
import subprocess
import json
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd2in13b_V4

# Setup directories
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'font')
if os.path.exists(libdir):
    sys.path.append(libdir)

# Load fonts
font_large_bold = ImageFont.truetype(os.path.join(fontdir, 'DejaVuSansMono-Bold.ttf'), 16) if os.path.exists(fontdir) else ImageFont.load_default()
font_medium = ImageFont.truetype(os.path.join(fontdir, 'DejaVuSansMono.ttf'), 12) if os.path.exists(fontdir) else ImageFont.load_default()
font_small = ImageFont.truetype(os.path.join(fontdir, 'DejaVuSansMono.ttf'), 10) if os.path.exists(fontdir) else ImageFont.load_default()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

api_url = 'http://localhost/api/stats/summary'
version_api_url = 'http://localhost/api/info/version'

def draw_progress_bar(draw_fill, draw_outline, x, y, w, h, percent, fill=0):
    fill_width = int(w * percent / 100)
    draw_fill.rectangle([x, y, x + fill_width, y + h], fill=fill)       # Filled portion in color
    draw_outline.rectangle([x, y, x + w, y + h], outline=0) 

def update(epd):
    W, H = epd.height, epd.width  # 250 x 122 landscape

    while True:
        # System Info
        ip = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True).strip().decode("utf-8")
        host = subprocess.check_output("hostname", shell=True).strip().decode() + ".local"
        mem_output = subprocess.check_output(dedent("free -m | awk 'NR==2{printf \"%s %s %.1f\", $3,$2,$3*100/$2 }'"), shell=True).decode("utf-8")
        mem_used, mem_total, mem_percent = mem_output.split()
        cpu_usage = float(subprocess.check_output(dedent("top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'"), shell=True).decode("utf-8").strip())
        disk_output = subprocess.check_output(dedent("df -m / | awk 'NR==2{printf \"%s %s %.1f\", $3,$2,$3*100/$2 }'"),shell=True).decode("utf-8")
        disk_used, disk_total, disk_percent = disk_output.split()
        disk_warning = float(disk_percent) > 75

        # Pi-hole Data (with fallback defaults)
        is_healthy = False
        percent_blocked = 0
        blocked = 0
        total = 0
        clients = 0
        update_available = False

        try:
            r = requests.get(api_url, timeout=3)
            if r.status_code == 200:
                data = r.json()
                percent_blocked = data['queries']['percent_blocked']
                blocked = data['queries']['blocked']
                total = data['queries']['total']
                clients = data['clients']['active']
                is_healthy = True
        except Exception as e:
            print(f"Failed to fetch Pi-hole data: {e}")

        try:
            r = requests.get(version_api_url, timeout=3)
            if r.status_code == 200:
                data = r.json()
                if data['version']['core']['local']['version'] != data['version']['core']['remote']['version']:
                    update_available = True
        except Exception as e:
            print(f"Failed to fetch Pi-hole version data: {e}")

        last_updated = f"u: {strftime('%H:%M')}"

        timestamp = strftime("%d/%m/%Y %H:%M:%S")
        logging.info(f"Last Updated: {timestamp}")
        logging.info(f"Host: {host}")
        logging.info(f"IP Address: {ip}")
        logging.info(f"CPU Usage: {cpu_usage:.1f}%")
        logging.info(f"Memory Used: {mem_used}MB / {mem_total}MB ({mem_percent}%)")
        logging.info(f"Disk Used: {disk_used}MB / {disk_total}MB ({disk_percent}%)")
        logging.info(f"Disk Warning (>75%): {'YES' if disk_warning else 'NO'}")
        logging.info(f"Pi-hole Healthy: {'YES' if is_healthy else 'NO'}")
        logging.info(f"Queries Blocked: {blocked}")
        logging.info(f"Total Queries: {total}")
        logging.info(f"Blocked Percentage: {percent_blocked:.1f}%")
        logging.info(f"Active Clients: {clients}")
        logging.info(f"Pi-hole Update Available: {'YES' if update_available else 'NO'}")

        # Image setup
        image_black = Image.new('1', (W, H), 255)
        image_red = Image.new('1', (W, H), 255)
        draw_black = ImageDraw.Draw(image_black)
        draw_red = ImageDraw.Draw(image_red)

        # Header
        draw_red.text((W // 2 - 30, 2), "Pi-hole", font=font_large_bold, fill=0)
        draw_black.text((5, 2), f"Clients: {clients}", font=font_small, fill=0)
        draw_black.text((W - 55, 2), last_updated, font=font_small, fill=0)

        # Host/IP
        host_ip_text = f"{host} ({ip})"
        host_ip_width = draw_black.textlength(host_ip_text, font=font_medium)
        draw_black.text(((W - host_ip_width) // 2, 20), host_ip_text, font=font_medium, fill=0)

        # Bar Layout
        bar_width = 90
        bar_height = 18
        left_x = 5
        right_x = W - bar_width - 5
        y_start = 45

        # RAM Bar
        draw_black.text((left_x, y_start), f"RAM: {mem_used}/{mem_total}MB ({mem_percent}%)", font=font_small, fill=0)
        draw_progress_bar(draw_red, draw_black, left_x, y_start + 13, bar_width, bar_height, float(mem_percent), fill=0)

        # CPU Bar
        draw_black.text((right_x, y_start), f"CPU: {cpu_usage:.1f}%", font=font_small, fill=0)
        draw_progress_bar(draw_red, draw_black, right_x, y_start + 13, bar_width, bar_height, cpu_usage, fill=0)

        # Blocked Percentage Bar (full width)
        bottom_y = H - 22
        draw_black.text((left_x, bottom_y - 12), f"Blocked: {blocked}", font=font_small, fill=0)
        draw_black.text((W // 2 - 15, bottom_y - 12), f"{percent_blocked:.1f}%", font=font_small, fill=0)
        draw_black.text((W - 90, bottom_y - 12), f"Total: {total}", font=font_small, fill=0)

        # warning messages
        if not is_healthy:
            down_msg = "Pi-Hole Down"
            msg_width = draw_black.textlength(down_msg, font=font_small)
            draw_black.text(((W - msg_width) // 2, bottom_y + 2), down_msg, font=font_small, fill=0)
            draw_progress_bar(draw_red, draw_black, left_x, bottom_y, W - 10, bar_height, 0, fill=0)
        elif disk_warning:
            down_msg = "Disk percentage above 75%"
            msg_width = draw_black.textlength(down_msg, font=font_small)
            draw_black.text(((W - msg_width) // 2, bottom_y + 2), down_msg, font=font_small, fill=0)
            draw_progress_bar(draw_red, draw_black, left_x, bottom_y, W - 10, bar_height, 0, fill=0)
        elif update_available:
            down_msg = "Update Available"
            msg_width = draw_black.textlength(down_msg, font=font_small)
            draw_black.text(((W - msg_width) // 2, bottom_y + 2), down_msg, font=font_small, fill=0)
            draw_progress_bar(draw_red, draw_black, left_x, bottom_y, W - 10, bar_height, 0, fill=0)
        else:
            draw_progress_bar(draw_red, draw_black, left_x, bottom_y, W - 10, bar_height, percent_blocked, fill=0)

        # Rotate for display
        image_black = image_black.rotate(180)
        image_red = image_red.rotate(180)
        epd.display(epd.getbuffer(image_black), epd.getbuffer(image_red))

        sleep_sec = 10 * 60
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
        logging.info("sleeping before leaving")
        epd.sleep()

if __name__ == '__main__':
    main()