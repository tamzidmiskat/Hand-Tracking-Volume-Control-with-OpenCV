import cv2
import mediapipe as mp
import time
import HandTrackingModule as htm
import numpy as np
from math import hypot # Import hypot for distance calculation

# Volume Control Imports (Ensure these are present at the top of the file)
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from pycaw.constants import EDataFlow, ERole # This must be imported

##################################
# Setup Camera and Hand Detector
##################################
wCam, hCam = 640, 480
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
detector = htm.handDetector(detectionCon=0.7) # Use the class from your module

##################################
# Volume Control Setup (pycaw)
##################################
# This method directly gets the default speaker interface (bypassing the GetAllDevices and device listing issues)
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)

volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]
vol = 0
volBar = 400
volPer = 0

##################################
# Main Loop
##################################
pTime = 0
while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)

    if len(lmList) != 0:
        # Get coordinates for tip of Thumb (4) and Index Finger (8)
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]

        # Draw circles at the tips and a line connecting them
        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

        # Calculate the length (distance) between thumb and index finger
        length = hypot(x2 - x1, y2 - y1)
        # print(length)
        # Hand range: 50 (close) - 300 (open). Your range might differ!
        # Volume range: minVol (-65.25) to maxVol (0.0)
        vol = np.interp(length, [50, 300], [minVol, maxVol])
        volBar = np.interp(length, [50, 300], [400, 150])
        volPer = np.interp(length, [50, 300], [0, 100])
        # print(int(length), vol)

        # Set the system volume
        volume.SetMasterVolumeLevel(vol, None)
        # Change circle color if fingers are close (min volume)
        if length < 50:
            cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)

    # Draw Volume Bar
    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_PLAIN, 2,
                (255, 0, 0), 3)

    # Calculate and Display FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (400, 70), cv2.FONT_HERSHEY_PLAIN, 3,
                (255, 0, 255), 3)

    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()