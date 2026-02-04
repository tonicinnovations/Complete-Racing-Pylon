#!/usr/bin/env python

import os
import time
from ApiClient import ApiClient
from Colors import Colors
from FlagStatus import FlagStatus
from Series import Series
from samplebase import SampleBase
from rgbmatrix import graphics
from PIL import Image

# Dictionary to map series to their corresponding badge directory numbers
series_badge_dir = {
    Series.CUP: '1',
    Series.XFINITY: '2',
    Series.TRUCKS: '3'
}

positionChange = {}

class RunText(SampleBase):
    def __init__(self, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)

    def flag(self, flag_status):
        if flag_status == FlagStatus.NONE:
            return ""
        elif flag_status == FlagStatus.GREEN:
            return Colors.GREEN + FlagStatus.GREEN.name + Colors.ENDC
        elif flag_status == FlagStatus.CAUTION:
            return Colors.YELLOW + FlagStatus.CAUTION.name + Colors.ENDC
        elif flag_status == FlagStatus.RED:
            return Colors.RED + FlagStatus.RED.name + Colors.ENDC
        elif flag_status == FlagStatus.WHITE:
            return Colors.WHITE + FlagStatus.WHITE.name + Colors.ENDC
        elif flag_status == FlagStatus.CHECKERED:
            return Colors.CHECKERED + FlagStatus.CHECKERED.name + Colors.ENDC
        elif flag_status == FlagStatus.ORANGE:
            return Colors.ORANGE + FlagStatus.ORANGE.name + Colors.ENDC
        return ""

    def run(self):
        series = Series.TRUCKS  # Change this to the desired series
        client = ApiClient()
        feed = client.getLiveFeed(series)
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        font = graphics.Font()
        font.LoadFont("../../../fonts/4x6.bdf")
        whiteColor = graphics.Color(255, 255, 255)
        greenColor = graphics.Color(0, 255, 0)
        redColor = graphics.Color(255, 0, 0)
        yellowColor = graphics.Color(255, 255, 0)

        # Use actual matrix dimensions
        matrix_width = self.matrix.width
        matrix_height = self.matrix.height

        # PANEL LAYOUT ASSUMPTION:
        # - 8 panels tall, each 32px high
        # - panel 1 (header) is at the *top* physically
        # - When we draw at y=0, it shows on panel 8 (bottom).
        # So: header must be drawn in the band [matrix_height-32 .. matrix_height-1].
        PANEL_HEIGHT = 32
        header_y_start = matrix_height - PANEL_HEIGHT       # top physical panel
        header_height = 14
        header_y_end = min(header_y_start + header_height, matrix_height)

        # Get the badge directory number based on the series
        badge_dir_number = series_badge_dir.get(series, '1')
        base_badge_path = '/home/tonicinnovations/badges'

        # Helper function to calculate text width
        def calculate_text_width(text):
            char_width = 4
            char_spacing = 1
            if not text:
                return 0
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
                bgColor = redColor  # Default color

            # ================= HEADER (now on physical panel 1) =================
            # Draw filled rectangle for header in that top band
            for y in range(header_y_start, header_y_end):
                graphics.DrawLine(offscreen_canvas, 0, y, matrix_width - 1, y, bgColor)

            # Create the text lines
            laps_text = f'{feed.lapsToGo} Laps'
            togo_text = "To Go"

            # Vertical positions inside that header band
            text_baseline_laps = header_y_start + 6
            text_baseline_togo = text_baseline_laps + 7

            # Calculate center positions for the text
            laps_text_pos = (matrix_width - calculate_text_width(laps_text)) // 2
            togo_text_pos = (matrix_width - calculate_text_width(togo_text)) // 2

            # Draw the header text
            graphics.DrawText(offscreen_canvas, font, laps_text_pos, text_baseline_laps, whiteColor, laps_text)
            graphics.DrawText(offscreen_canvas, font, togo_text_pos, text_baseline_togo, whiteColor, togo_text)

            # ================= VEHICLE LIST (unchanged for now) =================
            # Start position for the vehicle list as before (this will still be in the "old" area)
            top = 16

            for vehicle in feed.vehicles:
                previous_position = positionChange.get(vehicle.vehicleNumber, i)
                if previous_position < i:
                    textColor = redColor
                elif previous_position > i:
                    textColor = greenColor
                else:
                    textColor = whiteColor
                positionChange[vehicle.vehicleNumber] = i

                # Draw the position number
                graphics.DrawText(offscreen_canvas, font, 2, top + 8, whiteColor, f'{i}')

                # Construct the image path based on the series
                image_path = os.path.join(base_badge_path, badge_dir_number, f'{vehicle.vehicleNumber}.png')

                try:
                    badge_image = Image.open(image_path).convert('RGB')
                    badge_image = badge_image.resize((16, 16), Image.LANCZOS)
                    offscreen_canvas.SetImage(badge_image, 12, top)
                except IOError:
                    # If image not found, draw the car number as text
                    graphics.DrawText(offscreen_canvas, font, 12, top + 8, textColor, f'{vehicle.vehicleNumber:>2}')

                top += 16  # Adjust increment to fit more vehicles
                i += 1

                # Break after displaying 40 vehicles
                if i > 40:
                    break

                # Optionally implement scrolling if top exceeds matrix height
                if top > matrix_height - 16:
                    # Implement scrolling logic here if desired
                    break

            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
            time.sleep(2)
            feed = client.getLiveFeed(series)

if __name__ == "__main__":
    run_text = RunText()
    if not run_text.process():
        run_text.print_help()
