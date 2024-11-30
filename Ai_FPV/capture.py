#!/usr/bin/python3
# coding=utf8
import sys
import cv2
import time
import threading
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
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


range_rgb = {
    'red':   (0, 0, 255),
    'blue':  (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

lab_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

#find out the contour of the largest area
#parameter is the list of the contour to be compared
def getAreaMaxContour(contours) :
        contour_area_temp = 0
        contour_area_max = 0
        area_max_contour = None

        for c in contours : #traverse all the contour
            contour_area_temp = math.fabs(cv2.contourArea(c))  #calculate the contour area
            if contour_area_temp > contour_area_max:
                contour_area_max = contour_area_temp
                if contour_area_temp > 300:  #only when the area is more than 300, the contour with the largest area is effective so as to avoid interference
                    area_max_contour = c
        return area_max_contour, contour_area_max  #return the largest contour

def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

#set the color of RGB light on expansion board cosistent to match the color to be tracked 
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
    else:
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()

color_list = []
get_roi = False
detect_color = 'None'
start_pick_up = False

def init():
    print("ColorSorting Init")
    load_config()
    initMove()

rect = None
size = (320, 240)
roi = ()
last_x, last_y = 0, 0
draw_color = range_rgb["black"]

i = 0

def move():
    global detect_color
    global start_pick_up
    
    while True:
        
        if start_pick_up and detect_color != 'None':       
            setBuzzer(0.1)   #set buzzer to sound for 0.1s
            time.sleep(1.5)
            setBusServoPulse(1, 450, 500)
            time.sleep(1)
            AK.setPitchRangeMoving((-10, 0, 10), -90, -30, -90, 2000)
            time.sleep(2)
            AK.setPitchRangeMoving((-12, 0, 1), -90, -30, -90, 1000)
            time.sleep(1.5)
            setBusServoPulse(1, 200, 500)
            time.sleep(0.5)
            AK.setPitchRangeMoving((-10, 0, 10), -90, -30, -90, 1000)
            time.sleep(1)
            AK.setPitchRangeMoving((0, 10, 10), -90, -30, -90, 2000)
            time.sleep(2)
            
            detect_color = 'None'
            start_pick_up = False
                
        time.sleep(0.01)
    
    
# run child thread
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

def run(img):
    global roi,i
    global rect
    global get_roi
    global __isRunning
    global start_pick_up
    global last_x, last_y
    global detect_color, draw_color, color_list
        
    
    img_copy = img.copy()
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # convert the image into LAB color space
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
                                              lab_data[i]['max'][2]))  #perform bit operation on original image and the mask
                opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # open operation
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))  # close operation
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
                else:
                    color = 0
                color_list.append(color)
                if len(color_list) == 3:  # judge for multiple times
                    # take the average
                    color = int(round(np.mean(np.array(color_list))))
                    color_list = []
                    if color == 1:
                        start_pick_up = True
                        detect_color = 'red'
                        set_rgb(detect_color)
                        draw_color = range_rgb["red"]
                    elif color == 2:
                        start_pick_up = True
                        detect_color = 'green'
                        set_rgb(detect_color)
                        draw_color = range_rgb["green"]
                    elif color == 3:
                        start_pick_up = True
                        detect_color = 'blue'
                        set_rgb(detect_color)
                        draw_color = range_rgb["blue"]
                    else:
                        start_pick_up = False
                        detect_color = 'None'
                        set_rgb(detect_color)
                        draw_color = range_rgb["black"]               
        else:
            if not start_pick_up:
                draw_color = (0, 0, 0)
                detect_color = "None"
    
    cv2.putText(img, "Color: " + detect_color, (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, draw_color, 2)
    
    return img

if __name__ == '__main__':
    
    init()
    __target_color = ('red')
    cap = cv2.VideoCapture(-1) #read camera
    while True:
        ret,img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame)  
            frame_resize = cv2.resize(Frame, (320, 240))
            cv2.imshow('frame', frame_resize)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    my_camera.camera_close()
    cv2.destroyAllWindows()
