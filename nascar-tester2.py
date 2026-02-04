#!/usr/bin/env python

import os
import time
from ApiClient import ApiClient
from Colors import Colors
from FlagStatus import FlagStatus
from Series import Series

# Import SampleBase from the samplebase module
from samplebase import SampleBase
from rgbmatrix import graphics
from PIL import Image  # Added to handle image loading and manipulation

# CHANGE THIS TO SEE DIFFERENT SERIES DATA
positionChange = {}

class RunText(SampleBase):
    def __init__(self, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)

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

    def run(self):
        series = Series.CUP
        client = ApiClient()
        feed = client.getLiveFeed(series)
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        font = graphics.Font()
        font.LoadFont("../../../fonts/4x6.bdf")
        textColor = graphics.Color(255, 255, 255)
        whiteColor = graphics.Color(255, 255, 255)
        greenColor = graphics.Color(0, 255, 0)
        redColor = graphics.Color(255, 0, 0)
        yellowColor = graphics.Color(255, 255, 0)
        blueColor = graphics.Color(0, 0, 255)
        matrix_width = 32  # The width of the LED matrix

        # Helper function to calculate text width
        def calculate_text_width(text):
            char_width = 4
            char_spacing = 1
            return len(text) * char_width + (len(text) - 1) * char_spacing

        while feed.lapsToGo >= 0:
            offscreen_canvas.Clear()
            i = 1

            # Determine background color based on flag status
            if feed.flagStatus == FlagStatus.GREEN:
                bgColor = greenColor
            elif feed.flagStatus == FlagStatus.CAUTION:
                bgColor = yellowColor
            elif feed.flagStatus == FlagStatus.RED:
                bgColor = redColor
            else:
                bgColor = redColor  # Default color if no specific flag status

            # Draw background rectangle behind the "Laps" and "To Go" lines
            for y in range(0, 14):
                graphics.DrawLine(offscreen_canvas, 0, y, matrix_width - 1, y, bgColor)

            # Create the text lines
            laps_text = f'{feed.lapsToGo} Laps'
            togo_text = "To Go"
            top = 6  # Position text slightly lower to fit

            # Calculate the center positions for the text lines
            laps_text_pos = (matrix_width - calculate_text_width(laps_text)) // 2
            togo_text_pos = (matrix_width - calculate_text_width(togo_text)) // 2

            # Draw the "xxx Laps" text
            graphics.DrawText(offscreen_canvas, font, laps_text_pos, top, whiteColor, laps_text)
            top += 7  # Move down for the next line

            # Draw the "To Go" text
            graphics.DrawText(offscreen_canvas, font, togo_text_pos, top, whiteColor, togo_text)

            top += 10  # Move down for vehicle list

            for vehicle in feed.vehicles:
                my_text = f'{i:2} {vehicle.vehicleNumber:>2}'
                if positionChange.get(vehicle.vehicleNumber, i) < i:
                    textColor = redColor
                elif positionChange.get(vehicle.vehicleNumber, i) > i:
                    textColor = greenColor
                else:
                    textColor = whiteColor
                # Update new position
                positionChange[vehicle.vehicleNumber] = i

                print(my_text)

                # Draw the position number
                graphics.DrawText(offscreen_canvas, font, 2, top, whiteColor, f'{i}')

                # Load and display the badge image instead of the car number
                image_path = os.path.join('/home/tonicinnovations/badges', f'{vehicle.vehicleNumber}.png')
                try:
                    badge_image = Image.open(image_path)
                    # Resize the image if necessary (e.g., to 10x10 pixels)
                    badge_image = badge_image.resize((10, 10), Image.LANCZOS)
                    # Draw the image onto the canvas
                    offscreen_canvas.SetImage(badge_image, 21, top - 10)
                except IOError:
                    # If image not found, draw the car number as text
                    graphics.DrawText(offscreen_canvas, font, 21, top, textColor, f'{vehicle.vehicleNumber:>2}')

                top += 13
                i += 1

            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
            time.sleep(2)
            feed = client.getLiveFeed(series)

# Main function
if __name__ == "__main__":
    run_text = RunText()
    if (not run_text.process()):
        run_text.print_help()
