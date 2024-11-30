#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import math
import time
import threading
import numpy as np
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
import HiwonderSDK.TTS as TTS
import HiwonderSDK.yaml_handle as yaml_handle

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

AK = ArmIK()

# initial position
def initMove():
    Board.setBusServoPulse(1, 200, 300)
    Board.setBusServoPulse(2, 500, 500)
    AK.setPitchRangeMoving((0, 10, 10), -90, -30, -90, 1500)

try:
    tts = TTS.TTS()

except:
    print('sensor is not connected')

range_rgb = {
    'red':   (0, 0, 255),
    'blue':  (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'gray': (50,50,50),
    'white': (255, 255, 255)}

__target_color = ('red', 'green', 'blue')
detect_color = 'None'
garbage_species = 'None'

lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)
    
#set the color of RGB light on expansion board to match with the tracked color
def set_rgb(color):
    if color == "red":
        Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
        Board.RGB.show()
    elif color == "green":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
        Board.RGB.show()
    elif color == "blue":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
        Board.RGB.show()
    elif color == "gray":
        Board.RGB.setPixelColor(0, Board.PixelColor(50, 50, 50))
        Board.RGB.setPixelColor(1, Board.PixelColor(50, 50, 50))
        Board.RGB.show()
    else:
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()

# find the contour of the largest area
# parameter is a list of contour to be compared
def getAreaMaxContour(contours):
    
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None

    for c in contours:  # traverse all contours
        contour_area_temp = math.fabs(cv2.contourArea(c))  # calculate the area of contour
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 300:  # only when the area is more than 300, the contour of the largest area is effective so as to avoid inteference
                area_max_contour = c

    return area_max_contour, contour_area_max  # return the largest contour


def move():
    global detect_color
    
    while True:
        if detect_color == 'red':
            tts.TTSModuleSpeak("[h0][v10][m52]", "hazardous waste")
            time.sleep(2)
        elif detect_color == 'green':
            tts.TTSModuleSpeak("[h0][v10][m52]", "food waste")
            time.sleep(2)      
        elif detect_color == 'blue':
            tts.TTSModuleSpeak("[h0][v10][m52]", "recyclable waste")
            time.sleep(2)            
        elif detect_color == 'gray':
            tts.TTSModuleSpeak("[h0][v10][m52]", "other waste")
            time.sleep(2)
        detect_color = 'None'
        time.sleep(0.01)
      
# run child thread
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()


color_list = []
start_pick_up = False
size = (640, 480)
font_color = (0, 0, 0)
def run(img):
    global rect
    global font_color
    global detect_color
    global start_pick_up
    global color_list
    global garbage_species
        
    img_copy = img.copy()
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # convert image into LAB space
    color_area_max = None
    max_area = 0
    areaMaxContour_max = 0
    
    if not start_pick_up:
        for i in lab_data:
            if i in __target_color:
                frame_mask = cv2.inRange(frame_lab,
                                             (lab_data[i]['min'][0],
                                              lab_data[i]['min'][1],
                                              lab_data[i]['min'][2]),
                                             (lab_data[i]['max'][0],
                                              lab_data[i]['max'][1],
                                              lab_data[i]['max'][2]))  #perform bit operation on the original image and mask
                opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # open operation
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))  # closed operation
                contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  # find the contour
                areaMaxContour, area_max = getAreaMaxContour(contours)  # find the largest contour
                if areaMaxContour is not None:
                    if area_max > max_area:  # find the largest area
                        max_area = area_max
                        color_area_max = i
                        areaMaxContour_max = areaMaxContour
        
        if max_area > 500:  # the largest area is found
            rect = cv2.minAreaRect(areaMaxContour_max)
            box = np.int0(cv2.boxPoints(rect))
            
            cv2.drawContours(img, [box], -1, range_rgb[color_area_max], 2)
            if not start_pick_up:
                if color_area_max == 'red':  # color red is the largest
                    color = 1
                elif color_area_max == 'green':  # color green is the largest
                    color = 2
                elif color_area_max == 'blue':  # color blue is the largest
                    color = 3
                elif color_area_max == 'gray':  # color blue is the largest
                    color = 4
                else:
                    color = 0
                color_list.append(color)
                if len(color_list) == 20:  # judge for multiple times
                    # take the average
                    color = int(round(np.mean(np.array(color_list))))
                    color_list = []
                    
                    if color == 1:
                        font_color = (0, 0, 255)                
                        detect_color = 'red'
                        set_rgb(detect_color)
                        garbage_species = 'Hazardous Waste'
                    elif color == 2:
                        font_color = (0, 255, 0)
                        detect_color = 'green'                      
                        set_rgb(detect_color)
                        garbage_species = 'Food Waste'
                    elif color == 3:
                        font_color = (255, 0, 0)
                        detect_color = 'blue'
                        set_rgb(detect_color)
                        garbage_species = 'Recyclable'
                    elif color == 4:
                        font_color = (50, 50, 50)
                        detect_color = 'gray'                        
                        set_rgb(detect_color)
                        garbage_species = 'Residual Waste'
                    else:
                        font_color = (0, 0, 0)
                        detect_color = 'None'
                        set_rgb(detect_color)
       
    cv2.putText(img, "Color: " + garbage_species, (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, font_color, 2)
    return img

if __name__ == '__main__':
    initMove()
    cap = cv2.VideoCapture(-1) #read the camera
    __target_color = ('red', 'green', 'blue','gray')
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

        