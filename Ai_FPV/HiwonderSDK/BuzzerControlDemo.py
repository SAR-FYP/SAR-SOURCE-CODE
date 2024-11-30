import time
import Board

print('''
The below commands need to be used in LX terminal. LX terminal can be opened through pressing ctrl+alt+t.
Or click LX terminal icon at the top bar to open.
----------------------------------------------------------
Usage:
    sudo python3 BuzzerControlDemo.py
----------------------------------------------------------
Version: --V1.0  2020/08/12
----------------------------------------------------------
Tips:
 * ress Ctrl+C to close this program. If it fails, please try again.
----------------------------------------------------------
''')

Board.setBuzzer(0) # close

Board.setBuzzer(1) # open
time.sleep(0.1) # delay
Board.setBuzzer(0) #close

time.sleep(1) # delay

Board.setBuzzer(1)
time.sleep(0.5)
Board.setBuzzer(0)