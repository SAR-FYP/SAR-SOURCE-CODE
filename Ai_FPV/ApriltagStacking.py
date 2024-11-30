#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import math
import time
import threading
import numpy as np
import apriltag
import HiwonderSDK.Board as Board
import HiwonderSDK.Misc as Misc
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *

#apriltag stacking

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()

x = 0.0
y = 12.0
z = 5.0
st = True
tag_id = None
centerX = 340
centerY = 380
object_angle = 0
object_center_x = 0.0
object_center_y = 0.0

def reset():
    global x, y, z
    
    x = 0.0
    y = 12.0
    z = 5.0
    
# initial position
def initMove():
    Board.setBusServoPulse(1, 150, 800)
    Board.setBusServoPulse(2, 500, 800)
    AK.setPitchRangeMoving((x, y, z), -90,-90, 0, 1500)

def setBuzzer(s):
    Board.setBuzzer(1)
    time.sleep(s)
    Board.setBuzzer(0)
setBuzzer(0)
# detect apriltag
detector = apriltag.Detector(searchpath=apriltag._get_demo_searchpath())
def apriltagDetect(img):
    global object_center_x, object_center_y, object_angle
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    detections = detector.detect(gray, return_image=False)

    if len(detections) != 0:
        for detection in detections:                       
            corners = np.rint(detection.corners)  # acquire four angular points
            cv2.drawContours(img, [np.array(corners, np.int)], -1, (0, 255, 255), 2)
            tag_family = str(detection.tag_family, encoding='utf-8')  # obtain tag_family
            tag_id = int(detection.tag_id)  # acquire tag_id
            object_center_x, object_center_y = int(detection.center[0]), int(detection.center[1])  # center point
            object_angle = int(math.degrees(math.atan2(corners[0][1] - corners[1][1], corners[0][0] - corners[1][0])))  # calculate rotation angle
            angle = int(object_angle % 90)
            print(angle)
            return tag_family, tag_id   
    return None, None

def move():
    global x, y, z, st
    global object_center_x, object_center_y
    
    num = 0
    slow = True
    x_st = False
    y_st = False
    while True:
        if tag_id is not None:
            if (object_center_x - centerX) > 20: # robotic arm approaches the object on x axis 
                x += 0.2
            elif (object_center_x - centerX) < -20:
                x -= 0.2
            else:
                x_st = True
                
            if (object_center_y - centerY) > 5:   # robotic arm approaches the object on y axis
                y -= 0.1
            elif (object_center_y - centerY) < -10:
                y += 0.1
            else:
                y_st = True
                
            if slow:
                AK.setPitchRangeMoving((x, y, 3), -90,-90, 0, 800) # Move slowly for the first step after detection
                time.sleep(0.8)
                slow = False
            else:
                AK.setPitchRangeMoving((x, y, 3), -90,-90, 0, 100)
                time.sleep(0.1)
            
            if x_st and y_st:  #robotic arm is above the object
                st = False
                x_st = False
                y_st = False
                setBuzzer(0.1)
                angle = int(object_angle % 90) #read deflection angle of the object
                # convert the deflection angle into the pulse width of NO.2 servo
                if angle > 45:
                    angle = angle - 45
                    Servo2_Pulse = int(Misc.map(angle, 0, 45, 300, 500))
                else:
                    Servo2_Pulse = int(Misc.map(angle, 0, 45, 500, 700))
                Board.setBusServoPulse(2, Servo2_Pulse, 500) 
                time.sleep(0.5)
                # robotic arm starts picking
                AK.setPitchRangeMoving((x, y+1.6, 0), -90,-90, 0, 500)
                time.sleep(0.5)
                Board.setBusServoPulse(1, 450, 500)
                time.sleep(0.5)
                # lift after picking
                AK.setPitchRangeMoving((x, y, z), -90,-90, 0, 1500)
                time.sleep(1.5)
                # move to placing area above
                AK.setPitchRangeMoving((-12, 0, 2+3*num), -90,-90, 0, 1500)
                time.sleep(1.5)
                # adjust placing angle
                Board.setBusServoPulse(2, 500, 500)
                time.sleep(0.5)
                # place the object
                AK.setPitchRangeMoving((-12, 0, 3*num), -90,-90, 0, 1000)
                time.sleep(1)
                Board.setBusServoPulse(1, 150, 500)
                time.sleep(0.5)
                reset()
                # lift the robotic arm
                AK.setPitchRangeMoving((-y, x, 2+3*num), -90,-90, 0, 1000)
                time.sleep(1)
                # back to the position of detection
                AK.setPitchRangeMoving((x, y, z), -90,-90, 0, 1000)
                time.sleep(1)
                # adjust stacking height
                num += 1
                num = 0 if num > 2 else num
                st = True
                time.sleep(1)
        else:
            slow = True
            time.sleep(0.01)
    
# run child thread
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

def run(img):
    global state
    global tag_id
    global action_finish
    global object_center_x, object_center_y
     
    img_h, img_w = img.shape[:2]
    
    if st:
        tag_family, tag_id = apriltagDetect(img) # apriltag detection
    
        if tag_id is not None:
            cv2.putText(img, "tag_id: " + str(tag_id), (10, img.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, [0, 255, 255], 2)
            cv2.putText(img, "tag_family: " + tag_family, (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, [0, 255, 255], 2)
    else:
        cv2.putText(img, "tag_id: None", (10, img.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, [0, 255, 255], 2)
        cv2.putText(img, "tag_family: None", (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, [0, 255, 255], 2)
    
    return img

if __name__ == '__main__':
    
    initMove()
    cap = cv2.VideoCapture(-1) #read camera
    
    while True:
        ret, img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)           
            cv2.imshow('Frame', Frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    cv2.destroyAllWindows()
