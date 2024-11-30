import time
import Board

print('''
The below commands need to be used in LX terminal. LX terminal can be opened through pressing ctrl+alt+t.
Or click LX terminal icon at the top bar to open.
----------------------------------------------------------
Usage:
    sudo python3 BusServoMove.py
----------------------------------------------------------
Version: --V1.0  2020/08/12
----------------------------------------------------------
Tips:
 * Press Ctrl+C to close this program. If it fails, please try again. 
----------------------------------------------------------
''')

while True:
    # parameter：parameter 1：servo id; parameter 2：position; parameter 3：running time
    Board.setBusServoPulse(2, 500, 500) # NO.2 servo rotates to 500 position in 500ms
    time.sleep(0.5) # delay time is the same as the running time
    
    Board.setBusServoPulse(2, 200, 500) #Rotation range of the servo is 0-240 degree. The corresponding pulse width is 0-1000, so the range of parameter 2 is 0-1000.
    time.sleep(0.5)
    
    Board.setBusServoPulse(2, 500, 200)
    time.sleep(0.2)
    
    Board.setBusServoPulse(2, 200, 200)
    time.sleep(0.2)
    
    Board.setBusServoPulse(2, 500, 500)  
    Board.setBusServoPulse(3, 300, 500)
    time.sleep(0.5)
    
    Board.setBusServoPulse(2, 200, 500)  
    Board.setBusServoPulse(3, 500, 500)
    time.sleep(0.5)    
