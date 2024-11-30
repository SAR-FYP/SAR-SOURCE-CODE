#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import math
import time
import threading
import numpy as np
import HiwonderSDK.tm1640 as tm
import RPi.GPIO as GPIO
import HiwonderSDK.Board
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

AK = ArmIK()
AK.setPitchRangeMoving((0, 10, 3), -90, -30, -90, 1500)

color_range = {
'red': [(0, 101, 177), (255, 255, 255)], 
'green': [(47, 0, 135), (255, 119, 255)], 
'blue': [(0, 0, 0), (255, 255, 115)], 
'black': [(0, 0, 0), (41, 255, 136)], 
'white': [(193, 0, 0), (255, 250, 255)], 
}
## initialize the pin mode
fanPin1 = 22
fanPin2 = 24
GPIO.setup(fanPin1, GPIO.OUT) #set pin as output mode
GPIO.setup(fanPin2, GPIO.OUT)


if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)
    
range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

# find the contour with the largest area
# parameter is the list of contour to be compared
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None

    for c in contours:  # traverse all the contours
        contour_area_temp = math.fabs(cv2.contourArea(c))  # calculate the contour area
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 50:  # only when the area is more than 50, the contour of the largest area is effective, so as to avoid inteference.
                area_max_contour = c

    return area_max_contour, contour_area_max  # return the largest contour

shape_length = 0

def move():
    global shape_length
    
    while True:
        if shape_length == 3:
            print('triangle')
            ## display 'triangle'
            tm.display_buf = (0x80, 0xc0, 0xa0, 0x90, 0x88, 0x84, 0x82, 0x81,
                              0x81, 0x82, 0x84,0x88, 0x90, 0xa0, 0xc0, 0x80)
            tm.update_display()
            
        elif shape_length == 4:
            print('rectangle')
            ## display'rectangle'
            tm.display_buf = (0x00, 0x00, 0x00, 0x00, 0xff, 0x81, 0x81, 0x81,
                              0x81, 0x81, 0x81,0xff, 0x00, 0x00, 0x00, 0x00)
            tm.update_display()
            
        elif shape_length >= 6:           
            print('circle')
            ## display'circle'
            tm.display_buf = (0x00, 0x00, 0x00, 0x00, 0x1c, 0x22, 0x41, 0x41,
                              0x41, 0x22, 0x1c,0x00, 0x00, 0x00, 0x00, 0x00)
            tm.update_display()
            
        time.sleep(0.01)
       
        
# run child thread
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

shape_list = []
action_finish = True

if __name__ == '__main__':
    
    cap = cv2.VideoCapture(-1)
    while True:
        ret,img = cap.read()
        if ret:
            img_copy = img.copy()
            img_h, img_w = img.shape[:2]
            frame_gb = cv2.GaussianBlur(img_copy, (3, 3), 3)      
            frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # convert the image into LAB space
            max_area = 0
            color_area_max = None    
            areaMaxContour_max = 0

            if action_finish:
                for i in color_range:
                    if i != 'white':
                        frame_mask = cv2.inRange(frame_lab, color_range[i][0], color_range[i][1])  #perform bit operation on the original image and the mask
                        opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((6,6),np.uint8))  #open operation
                        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((6,6),np.uint8)) #closed operation
                        contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  #find the contour
                        areaMaxContour, area_max = getAreaMaxContour(contours)  #find the largest contour
                        if areaMaxContour is not None:
                            if area_max > max_area:#find the largest area
                                max_area = area_max
                                color_area_max = i
                                areaMaxContour_max = areaMaxContour
            if max_area > 200:                   
                cv2.drawContours(img, areaMaxContour_max, -1, (0, 0, 255), 2)
                # recognize shape
                # perimeter  0.035 Modify it according to the recognition effect，The better the recognition effect is, the smaller the value is.
                epsilon = 0.035 * cv2.arcLength(areaMaxContour_max, True)
                # approximate contour
                approx = cv2.approxPolyDP(areaMaxContour_max, epsilon, True)
                shape_list.append(len(approx))
                if len(shape_list) == 30:
                    shape_length = int(round(np.mean(shape_list)))                            
                    shape_list = []
                    print(shape_length)
                    
            frame_resize = cv2.resize(img, (320, 240))
            cv2.imshow('frame', frame_resize)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    my_camera.camera_close()
    cv2.destroyAllWindows()

