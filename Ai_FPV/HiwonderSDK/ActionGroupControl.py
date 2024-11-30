#!/usr/bin/env python3
# encoding: utf-8
import os
import time
import threading
import sqlite3 as sql
from HiwonderSDK.Board import *

runningAction = False
stopRunning = False
online_action_num = None
online_action_times = -1
update_ok = False
action_group_finish = True
 
def stop_servo():
    for i in range(16):
        stopBusServo(i+1) 

def stop_action_group():
    global stopRunning, online_action_num, online_action_times, update_ok
    update_ok = False
    stopRunning = True
    online_action_num = None
    online_action_times = -1
    time.sleep(0.1)

def action_finish():
    global action_group_finish
    return action_group_finish  

def runAction(actNum):
    '''
    run action group. Stop signal cannot be sent.
    :param actNum: name of action group, string type
    :param times:  running time
    :return:
    '''
    global runningAction
    global stopRunning
    global online_action_times
    if actNum is None:
        return
    actNum = "/home/ubuntu/Sensor/ActionGroups/" + actNum + ".d6a"
    stopRunning = False
    if os.path.exists(actNum) is True:
        if runningAction is False:
            runningAction = True
            ag = sql.connect(actNum)
            cu = ag.cursor()
            cu.execute("select * from ActionGroup")
            while True:
                act = cu.fetchone()
                if stopRunning is True:
                    stopRunning = False                   
                    break
                if act is not None:
                    for i in range(0, len(act)-2, 1):
                        setBusServoPulse(i+1, act[2 + i], act[1])
                    time.sleep(float(act[1])/1000.0)
                else:   # exit after running
                    break
            runningAction = False
            
            cu.close()
            ag.close()
    else:
        runningAction = False
        print("action group files cannot be found")

def online_thread_run_acting():
    global online_action_times, online_action_num, update_ok, action_group_finish
    while True:
        if update_ok:
            if online_action_times == 0:
                # unlimited running
                if action_group_finish:
                    action_group_finish = False
                runAction(online_action_num)                
            elif online_action_times > 0:
                # limited running
                if action_group_finish:
                    action_group_finish = False
                runAction(online_action_num)
                online_action_times -= 1    # after running, enter on load          
                if online_action_times == 0:
                    online_action_times = -1
            else:
                # no load
                if not action_group_finish:
                    action_group_finish = True
                time.sleep(0.001)
        else:
            if not action_group_finish:
                action_group_finish = True
            time.sleep(0.001)
            
def start_action_thread():
    th1 = threading.Thread(target=online_thread_run_acting)
    th1.setDaemon(True)  # set as background thread. Here is True by default.
    th1.start()
    
def change_action_value(actNum, actTimes):
    global online_action_times, online_action_num, update_ok, stopRunning, action_group_finish
    
    if action_group_finish:
        online_action_times = actTimes
        online_action_num = actNum
        stopRunning = False
        update_ok = True
