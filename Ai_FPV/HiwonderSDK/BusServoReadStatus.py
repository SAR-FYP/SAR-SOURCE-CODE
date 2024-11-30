import time
import Board

print('''
The below commands need to be used in LX terminal. LX terminal can be opened through pressing ctrl+alt+t.
Or click LX terminal icon at the top bar to open.
----------------------------------------------------------
Usage:
    sudo python3 BusServoReadStatus.py
----------------------------------------------------------
Version: --V1.0  2020/08/12
----------------------------------------------------------
Tips:
 * Press Ctrl+C to close this program. If it fails, please try again.
----------------------------------------------------------
''')

def getBusServoStatus():
    Pulse = Board.getBusServoPulse(2) # acquire position of NO.2 servo
    Temp = Board.getBusServoTemp(2) # acquiire temperature of NO.2 servo
    Vin = Board.getBusServoVin(2) # acquiire volatge of NO.2 servo
    print('Pulse: {}\nTemp:  {}\nVin:   {}\n'.format(Pulse, Temp, Vin)) # print status information
    time.sleep(0.5) # delay for checking

while True:   
    Board.setBusServoPulse(2, 500, 1000) # NO.2 servo rotaes to 500 position in 1000ms.
    time.sleep(1)
    getBusServoStatus()
    Board.setBusServoPulse(2, 300, 1000)
    time.sleep(1)
    getBusServoStatus()
