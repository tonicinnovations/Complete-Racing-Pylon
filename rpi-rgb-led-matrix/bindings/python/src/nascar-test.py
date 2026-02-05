#!/usr/bin/env python

import os
import time
from ApiClient import ApiClient
from Colors import Colors
from FlagStatus import FlagStatus
from Series import Series
from PIL import Image  # Import Pillow for image processing

# CHANGE THIS TO SEE DIFFERENT SERIES DATA

positionChange = {}

# Display a runtext with double-buffering.
from samplebase import SampleBase
from rgbmatrix import graphics
import time


class RunText(SampleBase):
    def __init__(self, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)
        self.parser.add_argument("-t", "--text", help="The text to scroll on the RGB LED panel", default="Hello world!")

    def flag(self, flag_status):
        if flag_status == FlagStatus.NONE:
            return ""
        elif flag_status == FlagStatus.GREEN:
            return Colors.GREEN + flag_status.GREEN.name + Colors.ENDC
        elif flag_status == FlagStatus.CAUTION:
            return Colors.YELLOW + flag_status.CAUTION.name + Colors.ENDC
        elif flag_status == FlagStatus.RED:
            return Colors.RED + flag_status.RED.name + Colors.ENDC
        elif flag_status == FlagStatus.WHITE:
            return flag_status.WHITE.name
        elif flag_status == FlagStatus.CHECKERED:
            return flag_status.CHECKERED.name
        elif flag_status == FlagStatus.ORANGE:
            return flag_status.ORANGE.name
        return ""

    def load_badge_image(self, series, vehicle_number):
        # Map series to directory
        series_dir = {
            Series.CUP: '1',
            Series.XFINITY: '2',
            Series.TRUCKS: '3'
        }
        # Build the file path
        badge_path = f'/home/tonicinnovations/badges/{series_dir[series]}/{vehicle_number}.png'

        try:
            # Open the image, convert to RGB format, and return it
            image = Image.open(badge_path).convert('RGB')
            return image
        except FileNotFoundError:
            print(f'Badge image not found for vehicle number: {vehicle_number}')
            return None

    def run(self):
        series = Series.CUP
        client = ApiClient()
        feed = client.getLiveFeed(series)
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        font = graphics.Font()
        font.LoadFont("../../../fonts/4x6.bdf")
        textColor = graphics.Color(255, 255, 255)
        whiteColor = graph
