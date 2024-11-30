#!/usr/bin/python3
# coding=utf8
import cv2
from pyzbar import pyzbar
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)
    
AK = ArmIK()
AK.setPitchRangeMoving((0, 10, 18), 0, -30, -90, 1500)


def run(image):
    # Find barcodes in image and decode each barcode
    barcodes = pyzbar.decode(image)
    # Loop through detected barcodes
    for barcode in barcodes:
        # extract the boarder position of barcode
        (x, y, w, h) = barcode.rect
        # draw the border of the bar code on the image
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)

        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        # draws barcode data and barcode type on the image
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    return image

if __name__ == '__main__':
    
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
