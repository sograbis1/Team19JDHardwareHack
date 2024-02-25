from picamera2 import Picamera2
import cv2
import numpy as np
from src import vehicle as vehicle_module
import gpiozero
from gpiozero import LED
import RPi.GPIO as GPIO
import time
led = LED(22)

vehicle = vehicle_module.Vehicle(
        {
            "motors": {
                "left": {
                    "pins": {
                        "speed": 13,
                        "control1": 5,
                        "control2": 6
                    }
                },
                "right": {
                    "pins": {
                        "speed": 12,
                        "control1": 7,
                        "control2": 8
                    }
                }
            }
        }
    )

HUE_VAL = 58    #targeted hue val

lower_color = np.array([HUE_VAL-10,100,100])    #upper color threshold
upper_color = np.array([HUE_VAL+10, 255, 255])    #lower color threshold

# Initializing and configuring camera
picam2 = Picamera2()
image_width = 400   #defiming image width
image_height = 200  #defining image height
center_image_x = image_width / 2    #center points of image along x and y
center_image_y = image_height / 2
picam2.preview_configuration.main.size = (image_width, image_height)  # Adjust the size as needed
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

#defining area bounds for object detection
minimum_area = 50
maximum_area = 550000    #tolerance for the robot to stop
#more calibration variables
#forward_speed = 1
#turn_speed = 0.7
forward_speed = 1
turn_speed = 0.3
#def turnOnLED

while True:

    image = picam2.capture_array()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    color_mask = cv2.inRange(hsv, lower_color, upper_color)   #steps from best_cv_alg program, getting the color mask for the specified hue

    contours, hierarchy = cv2.findContours(color_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)  #??
    cv2.imshow("Final Result", color_mask)
      #finding the largest contour

    object_area = 0
    object_x = 0
    object_y = 0

    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        found_area = width * height
        center_x = x + (width / 2)
        center_y = y + (height / 2)
        if object_area < found_area:
            object_area = found_area
            object_x = center_x
            object_y = center_y

    if object_area > 0:
        ball_location = [object_area, object_x, object_y]
    else:
        ball_location = None

  #at this point we have found the largest contour and stored it in ball_location

    if ball_location:
        if (ball_location[0] > minimum_area) and (ball_location[0] < maximum_area):
            if ball_location[1] > (center_image_x + (image_width/4)):
                vehicle.pivot_left(turn_speed)
                led.off()
                print("Turning left")
            elif ball_location[1] < (center_image_x - (image_width/4)):
                vehicle.pivot_right(turn_speed)
                led.off()
                print("Turning right")
            else:
                
                vehicle.drive_forward(forward_speed)
                time.sleep(0.3)
                print("Forward")
                led.on()
        elif (ball_location[0] < minimum_area):
            vehicle.pivot_left(turn_speed)
            led.off()
            print("Target isn't large enough, searching")
        else:
            vehicle.stop()
            led.on()
            print("Target large enough, stopping")
    else:
        vehicle.pivot_left(turn_speed)
        print("Target not found, searching")
        led.off()

  # Exit condition
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

# Clean up
picam2.stop()
cv2.destroyAllWindows()
