import numpy as np
from PIL import Image, ImageChops
import cv2
import os


prev = None
image_path = "C:/Users/Emily/Anaconda3/CARLA_0.9.5/PythonAPI/examples/_out/"
output = "C:/Users/Emily/Anaconda3/CARLA_0.9.5/PythonAPI/examples/new/"
hsv_path = "C:/Users/Emily/Anaconda3/CARLA_0.9.5/PythonAPI/examples/hsv/"
green_path = "C:/Users/Emily/Anaconda3/CARLA_0.9.5/PythonAPI/examples/green/"


def lane_diff(frame):
    image_list = os.listdir(image_path)
    # print(image_list)
    prev=int(frame)-1
    prev_frame='%08d' % prev
    prev=prev_frame+'.png'
    image=str(frame)+'.png'
    print(prev,image)
    if prev in image_list:
        
        img1 = Image.open(image_path + image).convert('RGB')
        img2 = Image.open(image_path + prev).convert('RGB')
        diff = ImageChops.difference(img1, img2)
        newout=output+frame+'_new.png'
        diff.save(newout,"PNG")

        diff = cv2.imread(newout)
        hsv = cv2.cvtColor(diff, cv2.COLOR_BGR2HSV)

        cv2.imwrite(hsv_path+frame+'_hsv.png', hsv)


        mask = cv2.inRange(hsv, (36,200,100), (70,255,255))

        imask = mask > 0 
        green = np.zeros_like(diff, np.uint8)
        green[imask] = diff[imask]

        cv2.imwrite(green_path+frame+"_green.png", green)
        green = cv2.imread(green_path+frame+"_green.png")
        h,s,v = cv2.split(green)
  
        return (cv2.countNonZero(s))

    return 0