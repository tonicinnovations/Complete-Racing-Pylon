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
        series = Series.CUP  # Change this to the desired series
        client = ApiClient()
        feed = client.getLiveFeed(series)
        offscreen_canvas = self.matrix.CreateFrameCanvas()

        # Load a small font
        font = graphics.Font()
        font.LoadFont("../../../fonts/5x7.bdf")
        whiteColor = graphics.Color(255, 255, 255)
        greenColor = graphics.Color(0, 255, 0)
        redColor = graphics.Color(255, 0, 0)
        yellowColor = graphics.Color(255, 255, 0)
        blackColor = graphics.Color(0, 0, 0)

        # Use actual matrix dimensions
        matrix_width = self.matrix.width
        matrix_height = self.matrix.height

        # Get the badge directory number based on the series
        badge_dir_number = series_badge_dir.get(series, '1')
        base_badge_path = '/home/tonicinnovations/badges'

        # Preload and resize badge images
        badge_images = {}
        for vehicle in feed.vehicles:
            image_path = os.path.join(base_badge_path, badge_dir_number, f'{vehicle.vehicleNumber}.png')
            try:
                badge_image = Image.open(image_path).convert('RGB')
                badge_image = badge_image.resize((5, 5), Image.NEAREST)
                badge_images[vehicle.vehicleNumber] = badge_image
            except IOError:
                badge_images[vehicle.vehicleNumber] = None  # Mark as missing

        # Calculate space per vehicle
        header_height = 16
        vehicle_height = 7  # Adjusted per vehicle
        available_height = matrix_height - header_height
        max_static_vehicles = min(available_height // vehicle_height, 30)

        # Implement scrolling for the remaining vehicles
        total_vehicles = len(feed.vehicles)
        scrolling_vehicles = feed.vehicles[max_static_vehicles:]

        # Helper function to calculate text width
        def calculate_text_width(text, font):
            width = 0
            for char in text:
                width += font.CharacterWidth(ord(char)) + 1  # Add 1 for spacing
            return width - 1  # Subtract extra spacing at the end

        while feed.lapsToGo >= 0:
            offscreen_canvas.Clear()

            # Determine text color based on flag status
            if feed.flagStatus == FlagStatus.GREEN:
                textColor = greenColor
            elif feed.flagStatus == FlagStatus.CAUTION:
                textColor = yellowColor
            elif feed.flagStatus == FlagStatus.RED:
                textColor = redColor
            else:
                textColor = whiteColor  # Default color

            # Create the text lines
            laps_text = f'{feed.lapsToGo} Laps'
            togo_text = "To Go"

            # Calculate center positions for the text
            laps_text_width = calculate_text_width(laps_text, font)
            togo_text_width = calculate_text_width(togo_text, font)
            laps_text_pos = (matrix_width - laps_text_width) // 2
            togo_text_pos = (matrix_width - togo_text_width) // 2

            # Draw the header text without background rectangle
            graphics.DrawText(offscreen_canvas, font, laps_text_pos, 6, textColor, laps_text)
            graphics.DrawText(offscreen_canvas, font, togo_text_pos, 13, textColor, togo_text)

            # Start position for the vehicle list
            top = header_height
            i = 1

            # Display the first 30 vehicles statically
            for vehicle in feed.vehicles[:max_static_vehicles]:
                # Draw the position number
                graphics.DrawText(offscreen_canvas, font, 2, top + 5, whiteColor, f'{i}')

                # Draw badge image or vehicle number
                badge_image = badge_images.get(vehicle.vehicleNumber)
                if badge_image:
                    offscreen_canvas.SetImage(badge_image, 10, top)
                else:
                    graphics.DrawText(offscreen_canvas, font, 10, top + 5, whiteColor, f'{vehicle.vehicleNumber}')

                top += vehicle_height
                i += 1

            # Display scrolling vehicles at the bottom
            if scrolling_vehicles:
                for scroll_vehicle in scrolling_vehicles:
                    # Draw the scrolling vehicle
                    graphics.DrawText(offscreen_canvas, font, 2, top + 5, whiteColor, f'{i}')
                    badge_image = badge_images.get(scroll_vehicle.vehicleNumber)
                    if badge_image:
                        offscreen_canvas.SetImage(badge_image, 10, top)
                    else:
                        graphics.DrawText(offscreen_canvas, font, 10, top + 5, whiteColor, f'{scroll_vehicle.vehicleNumber}')

                    # Swap the canvas to update the display
                    offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
                    time.sleep(2)  # Adjust scrolling speed

                    # Clear the scrolling vehicle for the next one
                    # Clear position number
                    graphics.DrawText(offscreen_canvas, font, 2, top + 5, blackColor, f'{i}')
                    # Clear badge image or vehicle number
                    if badge_image:
                        # Clear the image by drawing black lines over it
                        for y in range(top, top + 5):
                            graphics.DrawLine(offscreen_canvas, 10, y, 14, y, blackColor)
                    else:
                        graphics.DrawText(offscreen_canvas, font, 10, top + 5, blackColor, f'{scroll_vehicle.vehicleNumber}')

                    i += 1
            else:
                # Swap the canvas if no scrolling vehicles
                offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
                time.sleep(2)

            # Update feed
            feed = client.getLiveFeed(series)

    if __name__ == "__main__":
        run_text = RunText()
        if not run_text.process():
            run_text.print_help()

