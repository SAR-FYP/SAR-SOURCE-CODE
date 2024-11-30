import time
import Board
import signal

print('''
The below commands need to be used in LX terminal. LX terminal can be opened through pressing ctrl+alt+t.
Or click LX terminal icon at the top bar to open.
----------------------------------------------------------
Usage:
    sudo python3 RGBControlDemo.py
----------------------------------------------------------
Version: --V1.0  2020/08/12
----------------------------------------------------------
Tips:
 * Press Ctrl+C to close this program. If it fails, please try again.
----------------------------------------------------------
''')

start = True
#handle before closing
def Stop(signum, frame):
    global start

    start = False
    print('closing...')

#turn off all the lights
Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
Board.RGB.show()

signal.signal(signal.SIGINT, Stop)

while True:
    #set two lights as red
    Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
    Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
    Board.RGB.show()
    time.sleep(1)
    
    #set 2 lights as green
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
    Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
    Board.RGB.show()
    time.sleep(1)
    
    #set two lights as blue
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
    Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
    Board.RGB.show()
    time.sleep(1)
    
    #set two lights as yellow
    Board.RGB.setPixelColor(0, Board.PixelColor(255, 255, 0))
    Board.RGB.setPixelColor(1, Board.PixelColor(255, 255, 0))
    Board.RGB.show()
    time.sleep(1)

    if not start:
        #turn off all the light
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()
        print('closed')
        break
