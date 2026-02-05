#!/usr/bin/env python

import os
import time
from ApiClient import ApiClient
from Colors import Colors
from FlagStatus import FlagStatus
from Series import Series

def positionChangeSymbol(oldPostion, newPosition):
    return ""
    if (newPosition < oldPostion):
        return Colors.GREEN + "|" + Colors.ENDC
    elif (newPosition > oldPostion):
        return Colors.RED + "|" + Colors.ENDC
    else:
        return " "

def flag(flag):
    return ""
    if (flag == FlagStatus.NONE):
        return ""
    elif (flag == FlagStatus.GREEN):
        return Colors.GREEN + flag.GREEN.name + Colors.ENDC
    elif (flag == FlagStatus.CAUTION):
        return Colors.YELLOW + flag.CAUTION.name + Colors.ENDC
    elif (flag == FlagStatus.RED):
        return Colors.RED + flag.RED.name + Colors.ENDC
    elif (flag == FlagStatus.WHITE):
        return flag.WHITE.name
    elif (flag == FlagStatus.CHECKERED):
        return flag.CHECKERED.name
    elif (flag == FlagStatus.ORANGE):
        return flag.ORANGE.name

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
       
        
    def run(self):
        series = Series.CUP
        client = ApiClient()
        feed = client.getLiveFeed(series)
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        font = graphics.Font()
        font.LoadFont("../../../fonts/6x12.bdf")
        textColor = graphics.Color(255, 255, 255)
        whiteColor = graphics.Color(255, 255, 255)
        greenColor = graphics.Color(0, 255, 0)
        redColor = graphics.Color(255, 0, 0)
        blueColor = graphics.Color(0, 0, 255)
        pos = offscreen_canvas.width
        pos = 0
        my_text = self.args.text

        
        while feed.lapsToGo >= 0:
            offscreen_canvas.Clear()
            i = 1
            my_text=""
            top = 9
            len = graphics.DrawText(offscreen_canvas, font, pos, top, whiteColor, f'{feed.lapsToGo} ToGo')
            top += 13
            print(f'Laps {feed.lapNumber} Laps To Go {feed.lapsToGo} Flag {flag(feed.flagStatus)}')
            for vehicle in feed.vehicles:
                my_text == (f'{i:2} {vehicle.vehicleNumber:>2}')
                if positionChange.get(vehicle.vehicleNumber, i) < i:
                    textColor = redColor
                elif positionChange.get(vehicle.vehicleNumber, i) > i:  
                    textColor = greenColor
                else: 
                    textColor = whiteColor              
                # Update new postion
                positionChange[vehicle.vehicleNumber] = i
             
            
                print(my_text)
                
            
            
                len = graphics.DrawText(offscreen_canvas, font, pos, top, whiteColor, f'{i:2}')
                len = graphics.DrawText(offscreen_canvas, font, pos + 19, top, textColor, f'{vehicle.vehicleNumber:>2}')
                top = top + 13
                i += 1
            #pos -= 1
            #if (pos + len < 0):
            #    pos = offscreen_canvas.width

            
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
            time.sleep(2)
            feed = client.getLiveFeed(series)

# Main function
if __name__ == "__main__":
    run_text = RunText()
    if (not run_text.process()):
        run_text.print_help()


