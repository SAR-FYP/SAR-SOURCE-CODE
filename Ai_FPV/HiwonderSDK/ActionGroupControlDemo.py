import time
import Board
import ActionGroupControl as AGC

print('''
----------------------------------------------------------
The below command should be used in LX terminal. You can open LX terminal through ctrl+alt+t. 
Or click LX terminal icon on the top bar
----------------------------------------------------------
Usage:
    sudo python3 ActionGroupControlDemo.py
----------------------------------------------------------
Version: --V1.0  2020/08/12
----------------------------------------------------------
Tips:
 * Press Ctrl+C to close this program. If it fails, please try again. 
----------------------------------------------------------
''')

# The action group should be saved in this path, /home/pi/ArmPi/ActionGroups 
AGC.runAction('1') # This parameter is action group name without suffix. And it is passed in string
AGC.runAction('2')
